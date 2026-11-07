#!/usr/bin/env python3
"""Shared quota accounting + Gmail send lock for every outreach engine.

WHY THIS EXISTS (2026-11-07)
---------------------------
Three independent engines send cold email through ONE Gmail tab:
  * dayNN_wave_runner.py      - first-touch wave   (cron 20:00)
  * dayNN_chain_pitch.py      - corporate pitches  (cron 20:25)
  * dayNN_followup.py         - follow-ups         (cron 20:40)

Four bugs came from them each counting "sent today" their own way:

  BUG A - COUNTING ROWS, NOT EMAILS. A chain pitch is ONE email but
     `mark_sent()` stamps 'chain pitch sent' on EVERY tracked location of
     that brand (Brooklyn Fitboxing = 21 rows for 1 email). Counting rows
     inflated the day's total up to 13x and could make the quota look full
     when barely anything went out.
  BUG B - EACH ENGINE IGNORED THE OTHERS' SENDS. The wave counted only
     'email sent', the follow-up counted only 'email sent' + 'follow-up sent'
     and the chain pitch counted NOTHING at all. Three engines, three
     different numbers, one shared 100/day cap.
  BUG C - THE WAVE TOOK THE WHOLE ALLOWANCE. The wave was allowed to send
     all 100, so the chain pitch (20:25) and the follow-up engine (20:40)
     both saw 100/100 and ALWAYS deferred. The follow-up engine - 938
     eligible leads, the only thing that earns a reply - had never run.
  BUG D - TWO ENGINES SENDING AT ONCE. The wave sends 72 emails at ~38s
     pacing = ~46 minutes, so it was still running at 20:25 when the chain
     pitch fired. Both drive the SAME Gmail tab by clicking Compose, so they
     corrupt each other's drafts.

THE FIX
-------
1. A SEND LEDGER: /home/ubuntu/send_ledger.jsonl - one JSON line per ACTUAL
   email sent (day, engine, lead id or brand, timestamp). The ledger is the
   single source of truth for quota. CSV Status markers stay for per-lead
   resumability, but they are no longer used for counting.
2. ONE ALLOCATION, read from dayNN_quota_state.json:
       daily_email_quota  = 100   (hard cap, unchanged)
       followup_reserve   =  20
       chain_reserve      =   8
       wave allowance     = 100 - 20 - 8 = 72
3. A GMAIL SEND LOCK: /home/ubuntu/gmail_send.lock (exclusive create). Only
   one engine may hold the Gmail tab at a time; the others wait.

USAGE
-----
    from outreach_quota import claim_slot, record_send, release, wave_allowance

    n = wave_allowance()          # how many the wave may still send
    if not claim_slot('wave'):    # exclusive Gmail tab
        return                     # another engine is sending - come back later
    try:
        res = gmail_send(...)
        if res == 'sent':
            record_send('wave', lid)
    finally:
        release()
"""
import csv
import datetime
import errno
import glob
import json
import os
import time

LEADS_CSV = '/home/ubuntu/leads.csv'
LEDGER = '/home/ubuntu/send_ledger.jsonl'
LOCK = '/home/ubuntu/gmail_send.lock'
STATE_GLOB = '/home/ubuntu/day*_quota_state.json'

DEFAULT_QUOTA = 100
DEFAULT_FOLLOWUP_RESERVE = 20
DEFAULT_CHAIN_RESERVE = 8


# ---------------------------------------------------------------- state ----
def newest_state():
    """The newest dayNN_quota_state.json that has a date."""
    for s in sorted(glob.glob(STATE_GLOB), reverse=True):
        try:
            d = json.load(open(s))
            if d.get('date'):
                return d
        except Exception:
            continue
    return {}


def day_tag():
    """'2026-11-07' - the campaign day, never a hardcoded literal."""
    d = newest_state().get('date')
    return str(d) if d else datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')


def allocation():
    st = newest_state()
    daily = int(st.get('daily_email_quota', DEFAULT_QUOTA))
    fu = int(st.get('followup_reserve', DEFAULT_FOLLOWUP_RESERVE))
    ch = int(st.get('chain_reserve', DEFAULT_CHAIN_RESERVE))
    return {
        'daily': daily,
        'followup_reserve': fu,
        'chain_reserve': ch,
        'wave': max(0, daily - fu - ch),
    }


def wave_allowance():
    """How many first-touch emails the wave may still send today.

    Two limits, whichever is smaller:
      * the wave's own cap (daily - followup_reserve - chain_reserve) so it
        can never eat the whole allowance and starve the other engines
      * the absolute daily cap minus everything sent so far, so all three
        engines together can never exceed 100/day
    """
    a = allocation()
    used = sent_today()
    wave_used = sent_today(engine='wave')
    return max(0, min(a['wave'] - wave_used, a['daily'] - used))


def followup_allowance():
    """How many follow-ups may still go out today.

    The follow-up engine runs LAST (20:40), after the wave (20:00) and the
    chain pitches (20:25), so it takes whatever is left of the daily cap.
    The absolute daily cap is what actually stops the day going over 100.
    """
    a = allocation()
    used = sent_today()
    return max(0, a['daily'] - used)


def chain_allowance():
    """How many chain pitches may still go out today."""
    a = allocation()
    used = sent_today()
    chain_used = sent_today(engine='chain')
    return max(0, min(a['chain_reserve'] - chain_used, a['daily'] - used))


# ---------------------------------------------------------------- ledger ----
def ledger_entries():
    out = []
    try:
        with open(LEDGER, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
    except FileNotFoundError:
        pass
    return out


def sent_today(engine=None):
    """ACTUAL emails sent today, from the ledger.

    Counts EMAILS, not tracker rows - so one chain pitch that stamps 21
    location rows still counts as ONE email (BUG A).
    """
    day = day_tag()
    n = 0
    for e in ledger_entries():
        if e.get('day') != day:
            continue
        if engine and e.get('engine') != engine:
            continue
        n += 1
    return n


def record_send(engine, target, note=''):
    """Record one actual email sent. Call ONLY after gmail_send returned ok."""
    entry = {
        'day': day_tag(),
        'engine': engine,
        'target': target,
        'note': note,
        'ts': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    try:
        with open(LEDGER, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        print('LEDGER WRITE FAILED: %s' % e)
    return entry


def csv_sent_markers(day=None):
    """Fallback counter: rows whose Status marker carries a send action AND
    the day. Used only to seed the ledger for sends made before the ledger
    existed (so the cap is not reset by a restart)."""
    day = day or day_tag()
    n = 0
    try:
        with open(LEADS_CSV, newline='', encoding='utf-8-sig') as f:
            rows = list(csv.reader(f))
    except Exception:
        return 0
    if not rows:
        return 0
    try:
        si = rows[0].index('Status')
    except ValueError:
        return 0
    for r in rows[1:]:
        if len(r) <= si:
            continue
        for part in (r[si] or '').split('|'):
            low = part.lower()
            if ('email sent' in low or 'follow-up sent' in low) and day in part:
                n += 1
                break
    return n


def seed_ledger_from_csv(day=None):
    """One-time: if the ledger has no entry for this day but the CSV shows
    sends, write 'legacy' entries so the cap survives a restart."""
    day = day or day_tag()
    if any(e.get('day') == day for e in ledger_entries()):
        return 0
    n = csv_sent_markers(day)
    if n <= 0:
        return 0
    with open(LEDGER, 'a', encoding='utf-8') as f:
        for i in range(n):
            f.write(json.dumps({
                'day': day, 'engine': 'legacy-csv', 'target': 'row%d' % i,
                'note': 'seeded from leads.csv Status markers',
                'ts': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }, ensure_ascii=False) + '\n')
    return n


# ------------------------------------------------------------------ lock ----
def _lock_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError as e:
        return e.errno == errno.EPERM


def claim_slot(engine, wait_s=0, log=None):
    """Exclusive lock on the Gmail tab. Returns True if we got it."""
    for attempt in range(max(1, int(wait_s) + 1)):
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, ('%d %s' % (os.getpid(), engine)).encode())
            os.close(fd)
            return True
        except FileExistsError:
            try:
                raw = open(LOCK).read().strip()
                pid = int(raw.split()[0])
                if not _lock_alive(pid):
                    if log:
                        log('stale gmail lock (pid %s gone) - reclaiming' % pid)
                    os.unlink(LOCK)
                    continue
                if log:
                    log('gmail send lock held by pid %s (%s) - waiting' % (pid, raw))
            except Exception:
                pass
            if attempt < int(wait_s):
                time.sleep(30)
                continue
            return False
    return False


def release():
    try:
        os.unlink(LOCK)
    except FileNotFoundError:
        pass
    except Exception:
        pass


def lock_holder():
    try:
        return open(LOCK).read().strip()
    except Exception:
        return None
