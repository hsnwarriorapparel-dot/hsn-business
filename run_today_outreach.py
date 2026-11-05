#!/usr/bin/env python3
"""Run TODAY's outreach pipeline (the current dayNN_* orchestrator).

WHY THIS EXISTS (2026-11-04): the outreach cron job's prompt hardcoded
`day6_pipeline.py`, a script from 2026-10-19. Every night the agent had to
guess which dayNN_* files were current, and when the agent's own turn died
with a 429 the job restarted from ZERO instead of resuming the day's work.

This launcher removes the guesswork:
  * It resolves the CURRENT day tag from the date (no hardcoded day number).
  * It picks the newest matching dayNN_*.py family on disk.
  * It is IDEMPOTENT: the wave runner marks each lead 'email sent' in
    leads.csv the moment it succeeds, and this launcher SKIPS any wave lead
    already sent/failed/excluded. Re-running resumes; it never double-sends.
  * It refuses to start a SECOND pipeline for the same day while one is alive
    (exclusive lock), so a retry can never race the original.

Usage:
  run_today_outreach.py            # run today's pipeline (resumable)
  run_today_outreach.py --status   # report state, run nothing
"""
import argparse
import csv
import glob
import os
import re
import subprocess
import sys
import time

HOME = "/home/ubuntu"
CSV_PATH = os.path.join(HOME, "leads.csv")
LOCK_PATH = os.path.join(HOME, "outreach_pipeline.lock")
LOG_PATH = os.path.join(HOME, "outreach_pipeline.log")


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S") + " " + msg
    print(line, flush=True)
    try:
        with open(LOG_PATH, "a") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def find_python():
    cands = sorted(glob.glob(os.path.join(HOME, ".hermes/tools/python-3*/bin/python3")))
    return cands[0] if cands else sys.executable


def day_family():
    """The newest dayNN_* script family on disk -> (nn, orchestrator path)."""
    orchestrators = sorted(glob.glob(os.path.join(HOME, "day*_run.py")))
    if not orchestrators:
        return None, None
    newest = orchestrators[-1]
    nn = re.match(r"day(\d+)_run\.py$", os.path.basename(newest))
    return (nn.group(1) if nn else None), newest


def day_tag():
    """The date string the dayNN_* scripts use for today's status markers."""
    # The family on disk was built for a specific day; use the date that its
    # own quota-state file records, falling back to today.
    states = sorted(glob.glob(os.path.join(HOME, "day*_quota_state.json")),
                    key=os.path.getmtime)
    if states:
        try:
            import json
            with open(states[-1]) as fh:
                d = json.load(fh).get("date")
            if d:
                return d
        except Exception:
            pass
    return time.strftime("%Y-%m-%d")


def wave_file(nn):
    return os.path.join(HOME, f"day{nn}_wave.txt")


def pending_wave_leads(nn):
    """Wave leads that are NOT yet sent/failed/excluded (the resume set)."""
    wf = wave_file(nn)
    if not os.path.exists(wf):
        return 0, 0
    ids = [l.strip() for l in open(wf) if l.strip()]
    status = {}
    try:
        with open(CSV_PATH, encoding="utf-8-sig", errors="replace") as fh:
            for row in csv.DictReader(fh):
                status[(row.get("Lead ID") or "").strip()] = (row.get("Status") or "").lower()
    except Exception as exc:
        log(f"cannot read leads.csv: {exc}")
        return 0, 0
    pending = 0
    for lid in ids:
        st = status.get(lid, "")
        if "email sent" in st or "failed" in st or "excluded" in st or "re-hunt" in st:
            continue
        pending += 1
    return pending, len(ids)


def ammo():
    """Leads with an email and no send/fail/exclude marker."""
    n = 0
    try:
        with open(CSV_PATH, encoding="utf-8-sig", errors="replace") as fh:
            for row in csv.DictReader(fh):
                st = (row.get("Status") or "").lower()
                if not (row.get("Email") or "").strip():
                    continue
                if "email sent" in st or "failed" in st or "excluded" in st:
                    continue
                n += 1
    except Exception:
        pass
    return n


def pipeline_alive():
    """True when an orchestrator for this day is actually running.

    Match on the dayNN_run.py PROCESS, not on a substring of `ps aux`: a
    wrapper shell that merely MENTIONS the filename (a terminal call, a grep,
    this script's own command line) would otherwise look like a live pipeline.
    """
    try:
        out = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True,
                             text=True).stdout
    except Exception:
        return False
    for line in out.splitlines()[1:]:
        parts = line.strip().split(None, 1)
        if len(parts) != 2:
            continue
        pid, args = parts
        if not pid.isdigit():
            continue
        if int(pid) == os.getpid():
            continue
        # The real orchestrator: python <path>/dayNN_run.py
        if re.search(r"python\S*\s+\S*/day\d+_run\.py(\s|$)", args):
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true", help="report state, run nothing")
    ap.add_argument("--force", action="store_true", help="ignore the lock (dangerous)")
    args = ap.parse_args()

    nn, orchestrator = day_family()
    if not orchestrator:
        log("ERROR: no dayNN_run.py orchestrator found on disk")
        return 2

    pending, total = pending_wave_leads(nn)
    date = day_tag()
    log(f"=== outreach pipeline status ===")
    log(f"  family      : day{nn} ({os.path.basename(orchestrator)})")
    log(f"  day tag     : {date}")
    log(f"  wave        : {pending}/{total} lead(s) still pending")
    log(f"  ammo        : {ammo()} lead(s) with email and no send marker")
    log(f"  pipeline alive: {pipeline_alive()}")

    if args.status:
        return 0

    if pipeline_alive() and not args.force:
        log("a pipeline for this day is already running - NOT starting a second one")
        return 0

    # Exclusive lock so a retry can never race the original.
    lock_ok = False
    try:
        fd = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        lock_ok = True
    except FileExistsError:
        try:
            pid = int(open(LOCK_PATH).read().strip() or 0)
            os.kill(pid, 0)
            alive = True
        except (ProcessLookupError, ValueError, PermissionError, OSError):
            alive = False
        if alive:
            log(f"lock held by live pid {pid} - not starting a second pipeline")
            return 0
        os.unlink(LOCK_PATH)
        fd = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        lock_ok = True
    if lock_ok:
        log(f"lock acquired (pid {os.getpid()})")

    py = find_python()
    # TIMING (measured 2026-11-05): site-verify + wave build 75s, email wave
    # 100 leads @38s = 87 min, IG handle hunts 11 min, IG follow+DM pass over
    # 240 candidates = 2h21m, tracker rebuild ~1s. Total ~6h25m - so the old
    # 4h cap killed the run during the IG pass, every night. The cap must
    # cover the whole chain plus the reply sweep.
    timeout_s = int(os.environ.get("OUTREACH_TIMEOUT_S", "36000"))  # 10h
    log(f"launching: {py} {orchestrator} (timeout {timeout_s}s)")
    try:
        rc = subprocess.run([py, orchestrator], cwd=HOME, timeout=timeout_s).returncode
        log(f"orchestrator exited rc={rc}")
    except subprocess.TimeoutExpired:
        log(f"orchestrator TIMEOUT after {timeout_s}s - the work is resumable; "
            f"re-run this launcher to continue")
        rc = 124
    finally:
        try:
            if os.path.exists(LOCK_PATH):
                os.unlink(LOCK_PATH)
                log("lock released")
        except Exception:
            pass

    pend, tot = pending_wave_leads(nn)
    log(f"final: {pend}/{tot} wave lead(s) still pending")
    return 0


if __name__ == "__main__":
    sys.exit(main())
