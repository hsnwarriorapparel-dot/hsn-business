#!/usr/bin/env python3
"""Make sure TODAY's quota-state file exists and is correct.

WHY THIS EXISTS (2026-11-07)
-----------------------------
Every engine reads `dayNN_quota_state.json` for the campaign day, the daily
quota and the reserve slices. The day tag comes from the NEWEST state file
on disk - so if yesterday's file is still the newest one, every engine keeps
yesterday's day tag and the day's send count never resets. The 100/day cap
would be spent for good and outreach would stop permanently.

Nothing was creating the new day's file. This script does it, and it is
called first by the daily pipeline.

It also carries the allocation forward:
    daily_email_quota  = 100
    followup_reserve   =  20
    chain_reserve      =   8
so the wave gets 72 and the reply engines keep their reserved slices.
"""
import datetime
import glob
import json
import os
import sys

HOME = '/home/ubuntu'
PREFIX = 'day'


def newest_state():
    files = sorted(glob.glob(os.path.join(HOME, 'day*_quota_state.json')))
    for f in reversed(files):
        try:
            d = json.load(open(f))
            if d.get('date'):
                return f, d
        except Exception:
            continue
    return None, {}


def main():
    # QUOTA_STATE_TODAY overrides the campaign date (used by the rollover test).
    today = os.environ.get('QUOTA_STATE_TODAY') or \
        datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
    prev_file, prev = newest_state()

    # Is there already a state file for today?
    for f in sorted(glob.glob(os.path.join(HOME, 'day*_quota_state.json'))):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        if d.get('date') == today:
            # make sure the allocation fields are present
            changed = False
            for k, v in (('daily_email_quota', 100), ('followup_reserve', 20),
                         ('chain_reserve', 8), ('emails_sent_today_before_wave', 0)):
                if k not in d:
                    d[k] = v
                    changed = True
            if changed:
                json.dump(d, open(f, 'w'), indent=2)
                print('updated allocation fields in', os.path.basename(f))
            else:
                print('today\'s quota state already exists:', os.path.basename(f))
            print('  date=%s quota=%s reserves followup=%s chain=%s'
                  % (d.get('date'), d.get('daily_email_quota'),
                     d.get('followup_reserve'), d.get('chain_reserve')))
            return 0

    # Create a new one, carrying the allocation forward.
    num = 0
    for f in sorted(glob.glob(os.path.join(HOME, 'day*_quota_state.json'))):
        try:
            n = int(os.path.basename(f).replace('day', '').split('_')[0])
            num = max(num, n)
        except Exception:
            continue
    new_name = os.path.join(HOME, 'day%d_quota_state.json' % (num + 1))

    state = {
        'date': today,
        'daily_email_quota': 100,
        'followup_reserve': 20,
        'chain_reserve': 8,
        'emails_sent_today_before_wave': 0,
        'remaining_allowance': 100,
        'wave_size': 72,
        'verified_in_gmail': False,
        'created_by': 'ensure_quota_state.py',
        'carried_from': os.path.basename(prev_file) if prev_file else None,
        'allocation_note': (
            'New campaign day %s. The 100/day hard cap is SPLIT so every engine '
            'runs: first-touch wave 72, follow-up engine 20 reserved, chain/franchise '
            'corporate pitches 8 reserved. The wave caps itself at quota minus the '
            'reserves, and every send re-reads the shared ledger (send_ledger.jsonl), '
            'so the three engines can never exceed 100 together.' % today),
        'hunt_needed': False,
        'hunt_note': ('Fresh lead hunt runs automatically before the wave when the ammo '
                      'pool is below the daily target (dayNN_run.py).'),
    }
    json.dump(state, open(new_name, 'w'), indent=2)
    print('created %s for %s' % (os.path.basename(new_name), today))
    print('  wave allowance = 72 (100 - 20 followup - 8 chain)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
