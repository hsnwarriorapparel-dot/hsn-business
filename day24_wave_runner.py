#!/usr/bin/env python3
"""Day-22 (2026-11-05) email wave runner.

Resumable: skips any lead already marked 'email sent', marks each lead's
Status IMMEDIATELY after its send (row-targeted read -> write -> atomic
replace), so a re-run never double-sends. Checks Gmail readiness before every
send and stops cleanly (leaving the rest queued) if the tab goes bad.

Usage:
  day24_wave_runner.py            # send the whole wave
  day24_wave_runner.py --limit N  # send only the first N (foreground test)
"""
import sys, os, time, csv, tempfile, argparse
sys.path.insert(0, '/home/ubuntu')
from outreach import gmail_send
from templates import build_email
from cdp_helper import get_tabs, connect, js_eval

CSV = '/home/ubuntu/leads.csv'
LOG = '/home/ubuntu/day24_log.txt'
WAVE = '/home/ubuntu/day24_wave.txt'
PACE = 38

# The day tag MUST come from the quota-state file, never a hardcoded literal
# (fix 2026-11-06). Copied from day22 the literal stayed 'Daily 2026-11-05',
# so the runner counted day22's 100 emails as 'already sent today' and
# refused to send anything on a fresh day with 0 sends. Read the state file
# for the date; fall back to today (UTC) only if it is missing.
try:
    import json as _json0
    _st0 = _json0.load(open('/home/ubuntu/day24_quota_state.json'))
    DAY = 'Daily ' + str(_st0.get('date') or time.strftime('%Y-%m-%d', time.gmtime()))
except Exception:
    DAY = 'Daily ' + time.strftime('%Y-%m-%d', time.gmtime())

ap = argparse.ArgumentParser()
ap.add_argument('--limit', type=int, default=0)
ap.add_argument('--wave', default=WAVE, help='wave file (default: %s)' % WAVE)
ap.add_argument('--day', default=DAY, help='day tag written into Status')
args = ap.parse_args()
WAVE = args.wave
DAY = args.day


def log(m):
    line = time.strftime('%H:%M:%S') + ' ' + m
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')


def load():
    with open(CSV, newline='', encoding='utf-8-sig') as f:
        return list(csv.reader(f))


def update_status(lead_id, new_status):
    """Append a status marker to one lead.

    Routed through leads_safe_write.update_row(), which takes the leads.csv
    lock and re-reads at write time. The old version wrote the whole file
    back with no lock, so a row added by the ammo hunt or a reacher between
    its read and its write was silently destroyed.
    """
    import sys as _sys
    _sys.path.insert(0, '/home/ubuntu')
    from leads_safe_write import update_row
    update_row(lead_id, 'Status', new_status, append=True)


def already_sent(lid):
    rows = load()
    idx = {h: i for i, h in enumerate(rows[0])}
    for r in rows[1:]:
        if r and r[0] == lid:
            return 'email sent' in (r[idx['Status']] or '').lower()
    return False


def gmail_ready():
    try:
        tabs = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
        if not tabs:
            return False, 'no-gmail-tab'
        ws = connect(tabs[0])
        v = js_eval(ws, """(() => {
          const btn = Array.from(document.querySelectorAll('div[role="button"], .T-I')).find(e => /^Compose$/i.test((e.innerText||'').trim()));
          return btn ? 'ready' : 'no-compose-button';
        })()""", await_promise=False)
        ws.close()
        return v == 'ready', v
    except Exception as e:
        return False, f'probe-error:{str(e)[:60]}'


ids = [l.strip() for l in open(WAVE) if l.strip()]
if args.limit:
    ids = ids[:args.limit]

_rows0 = load()
_idx0 = {h: i for i, h in enumerate(_rows0[0])}

# DAILY QUOTA GUARD (2026-11-05): the user's hard limit is 100 cold emails per
# calendar day ACROSS every sender. The 09:00 system-cron (daily_automation_full.py)
# already sent 50 emails today - mostly to junk telemetry addresses, but they
# still count against the quota and against the sending-domain reputation.
# Count what went out today (any status carrying today's date) and cap the wave
# at the remaining allowance. Never exceed it.
# SHARED QUOTA LEDGER + GMAIL LOCK (2026-11-07). See outreach_quota.py for
# the four bugs this fixes. The wave no longer counts CSV rows - it counts
# actual emails in send_ledger.jsonl, and it takes the exclusive Gmail lock
# so it cannot collide with the chain-pitch or follow-up engines.
import sys as _sys
_sys.path.insert(0, '/home/ubuntu')
from outreach_quota import (claim_slot, release, record_send, sent_today,
                            wave_allowance, allocation, lock_holder)

QUOTA_STATE = '/home/ubuntu/day24_quota_state.json'
try:
    import json as _json
    _qs = _json.load(open(QUOTA_STATE))
    DAILY_EMAIL_QUOTA = int(_qs.get('daily_email_quota', 100))
    PRE_SENT_TODAY = int(_qs.get('emails_sent_today_before_wave', 0))
except Exception:
    DAILY_EMAIL_QUOTA = 100
    PRE_SENT_TODAY = 0
# COUNT ONLY REAL SEND MARKERS (fix 2026-11-06): the old check was
# `DAY in _st`, which matched the date ANYWHERE in the Status string - so the
# lead-source stamp 'HUNTED (gmaps 2PM 2026-11-06)' counted as a send for
# 2026-11-06. The wave then saw 100 'already sent' and refused to send
# anything on a day with 0 emails sent (Gmail confirmed 0). A row counts as
# sent today ONLY when the SAME marker carries both the send action and the
# day tag.
_today_sent = 0
for _r in _rows0[1:]:
    _st = (_r[_idx0['Status']] if _idx0['Status'] < len(_r) else '') or ''
    for _part in _st.split('|'):
        if 'email sent' in _part.lower() and DAY in _part:
            _today_sent += 1
            break
# QUOTA RESERVATION (2026-11-07): the first-touch wave used to be allowed to
# eat the ENTIRE 100/day allowance. Then the chain pitch (20:25) and the
# follow-up engine (20:40) both checked the quota, saw 100/100, and ALWAYS
# deferred - so the follow-up engine (938 eligible leads, the only thing that
# earns a reply) never ran, not once.
#
# The wave now only gets the allowance MINUS the reserved slices:
#   followup_reserve = 20  (follow-up engine - the reply engine)
#   chain_reserve    =  8  (chain/franchise corporate pitches - 8 brands)
# All three engines read the SAME allocation from ONE place and count the
# SAME ledger, so they can never drift or overshoot together.
_alloc = allocation()
FOLLOWUP_RESERVE = _alloc['followup_reserve']
CHAIN_RESERVE = _alloc['chain_reserve']
RESERVED = FOLLOWUP_RESERVE + CHAIN_RESERVE
# count from the shared ledger (actual emails), not CSV rows
_already = sent_today()
_remaining = max(0, _alloc['wave'] - _already)
log(f"DAY24 WAVE START: {len(ids)} leads from {WAVE}")
log(f"QUOTA: {_already} sent today (incl. {PRE_SENT_TODAY} pre-wave) | limit {DAILY_EMAIL_QUOTA} | reserved {RESERVED} (followup {FOLLOWUP_RESERVE} + chain {CHAIN_RESERVE}) | wave allowance {_remaining}")
if _remaining <= 0:
    log(f"DAILY EMAIL QUOTA ALREADY REACHED ({_already}/{DAILY_EMAIL_QUOTA}) - nothing sent")
    raise SystemExit(0)

# FILTER ALREADY-SENT LEADS *BEFORE* TRIMMING TO THE QUOTA (2026-11-05 fix):
# the old order trimmed `ids` to the allowance FIRST, so a resumed wave always
# re-picked the FIRST N wave ids - all of which were already sent - and the
# wave reported "50 skipped, 0 sent" forever. Filter first, then trim.
def _is_sent(lid):
    for _r in _rows0[1:]:
        if _r and _r[0] == lid:
            _st = (_r[_idx0['Status']] if _idx0['Status'] < len(_r) else '') or ''
            return 'email sent' in _st.lower()
    return False

_before = len(ids)
ids = [i for i in ids if not _is_sent(i)]
_removed = _before - len(ids)
if _removed:
    log(f"  filtered {_removed} already-sent lead(s) from the wave before trimming")
if len(ids) > _remaining:
    log(f"wave trimmed {len(ids)} -> {_remaining} to respect the daily quota")
    ids = ids[:_remaining]

# EXCLUSIVE LOCK (added 2026-11-05): two wave runners on one Gmail tab send
# the same lead twice and race on leads.csv. The lock file also tells the
# system-crontab wave_guard that this wave is owned, so it does not spawn a
# competitor. Stale locks (pid gone) are reclaimed.
LOCK = '/home/ubuntu/' + os.path.basename(WAVE).replace('_wave.txt', '_wave.lock')
lock_ok = False
try:
    fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    lock_ok = True
except FileExistsError:
    try:
        pid = int(open(LOCK).read().strip() or 0)
        os.kill(pid, 0)   # raises if the owner is gone
        alive = True
    except (ProcessLookupError, ValueError, PermissionError):
        alive = False
    if alive:
        log(f"  LOCK HELD by another runner (pid {pid}) - exiting to avoid a double-send race")
        raise SystemExit(0)
    os.unlink(LOCK)      # stale lock
    fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    lock_ok = True
if lock_ok:
    log(f"  wave lock acquired ({LOCK})")

rows = load()
idx = {h: i for i, h in enumerate(rows[0])}
iE, iN, iC, iCi, iS = (idx['Email'], idx['Name'], idx['Country'], idx['City'], idx['Status'])
meta = {r[0]: r for r in rows[1:] if r and r[0] in ids}

# GMAIL TAB LOCK (2026-11-07): the chain-pitch engine (20:25) and the
# follow-up engine (20:40) drive the SAME Gmail tab by clicking Compose. The
# wave sends 72 emails at ~38s pacing = ~46 minutes, so it is still running
# when the chain pitch fires. Without this lock the two processes corrupt
# each other's drafts. The wave holds the tab for its whole run.
if not claim_slot('wave', log=log):
    log(f"  GMAIL TAB BUSY (held by {lock_holder()}) - exiting, the wave resumes from the next tick")
    raise SystemExit(0)
log('  gmail send lock acquired')

sent = failed = skipped = 0
def _rows_now():
    """Fresh read of leads.csv - the send loop re-checks the live quota, and
    a stale in-memory copy would miss markers written by a concurrent runner."""
    import csv as _c
    with open(CSV, newline='', encoding='utf-8-sig') as _f:
        return list(_c.reader(_f))

for pos, lid in enumerate(ids, 1):
    r = meta.get(lid)
    if not r:
        log(f"  SKIP {lid}: not in CSV")
        skipped += 1
        continue
    if already_sent(lid):
        log(f"  SKIP {lid} ({(r[iN] or '')[:20]}): already marked email sent")
        skipped += 1
        continue
    ok_gmail, state = gmail_ready()
    if not ok_gmail:
        log(f"  GMAIL NOT READY ({state}) at {lid} - stopping, will resume from here")
        log(f"PAUSED after {sent} sent, {failed} failed, {skipped} skipped")
        break

    # RE-CHECK THE QUOTA IMMEDIATELY BEFORE EVERY SEND (fix 2026-11-06).
    # The quota was only computed ONCE at startup, so two concurrent runners
    # (the system-crontab wave_guard's runner + the orchestrator's runner)
    # both passed the same check and the day went to 101/100. Re-reading the
    # CSV here means the second runner sees the first runner's new markers
    # and stops instead of overshooting.
    # The ledger counts ACTUAL emails sent by ALL engines today.
    _live = sent_today()
    _wave_cap = max(0, DAILY_EMAIL_QUOTA - RESERVED)
    if _live >= _wave_cap:
        log(f"  WAVE CAP REACHED ({_live}/{_wave_cap} = quota {DAILY_EMAIL_QUOTA} minus reserved {RESERVED}) at {lid} - stopping, remaining stay queued")
        log(f"PAUSED after {sent} sent, {failed} failed, {skipped} skipped")
        break

    name = (r[iN] or '').strip().replace('&', 'and')
    email = (r[iE] or '').strip().lower()
    country = (r[iC] or '').strip() or 'Europe'
    city = (r[iCi] or '').strip()
    region = 'USA' if country.upper() in ('USA', 'UNITED STATES', 'US') else 'Europe'
    detail = f"martial arts and boxing gym in {city}" if city else f"martial arts and boxing gym in {country}"
    try:
        subject, body = build_email(name, detail, region=region)
        res = gmail_send(email, subject, body)
        ok = res.get('ok') if isinstance(res, dict) else ('sent' in str(res).lower())
        log(f"  [{pos}/{len(ids)}] EMAIL {lid} {name[:22]} -> {email}: {'OK' if ok else str(res)[:60]}")
        if ok:
            update_status(lid, f"COMPLETE: email sent ({DAY})")
            record_send('wave', lid, name[:40])
            sent += 1
        else:
            update_status(lid, f"EMAIL FAILED ({DAY}): {str(res)[:40]}")
            failed += 1
    except Exception as e:
        log(f"  [{pos}/{len(ids)}] EMAIL ERR {lid}: {str(e)[:70]}")
        update_status(lid, f"EMAIL FAILED ({DAY}): exception {str(e)[:20]}")
        failed += 1
    time.sleep(PACE)

release()   # free the Gmail tab for the chain-pitch / follow-up engines
log(f"DAY24 WAVE COMPLETE: {sent} sent, {failed} failed, {skipped} skipped")

# release the lock so the guard can resume a truncated wave later
try:
    if os.path.exists(LOCK):
        os.unlink(LOCK)
        log('wave lock released')
except Exception as e:
    log('lock release warning:', str(e)[:60])
