#!/usr/bin/env python3
"""Retry the 4 USA emails that failed with 'no-gmail-tab' during the Gmail outage.
Gmail is logged in again. Uses same template as the original Day-5 wave."""
import sys, time, csv
sys.path.insert(0, '/home/ubuntu')
from outreach import gmail_send
from templates import build_email
import safe_csv_update

CSV = '/home/ubuntu/leads.csv'
LOG = '/home/ubuntu/day5_email_retry4.log'

def log(m):
    line = f"{time.strftime('%H:%M:%S')} {m}"
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + "\n")

RETRY = [
    ('L373', 'Centralparkboxing', 'info@centralparkboxing.com', 'boxing gym New York'),
    ('L374', 'Gangupboxing', 'info@gangupboxing.com', 'boxing gym New York'),
    ('L375', 'Trinityboxing', 'nyc@trinityboxing.com', 'boxing gym New York'),
    ('L376', 'Boutfightclub', 'info@boutfightclub.com', 'boxing gym New York'),
]

def main():
    with open(CSV) as f:
        rows = list(csv.DictReader(f))
    by_id = {r['Lead ID']: r for r in rows}
    ok, fail = 0, 0
    for lid, name, email, detail in RETRY:
        r = by_id[lid]
        # keep prior IG status, replace the EMAIL FAILED segment
        prior = r['Status']
        base = prior.split(' - IG fallback')[0].replace('EMAIL FAILED: no-gmail-tab', '').strip()
        subject, body = build_email(name, detail, region='USA')
        try:
            res = gmail_send(email, subject, body)
            if res == 'sent' or 'sent' in str(res):
                new_status = f"COMPLETE: email sent (Day 5 USA wave retry)" + (f" | {' | '.join(prior.split(' - IG fallback')[1].strip().split(' | ')[0:])}" if ' - IG fallback' in prior else '')
                # simpler: keep IG part if present
                if 'IG follow' in prior:
                    ig_part = prior.split(' - IG fallback')[1].strip()
                    new_status = f"COMPLETE: email sent (Day 5 USA wave retry) | {ig_part}"
                else:
                    new_status = "COMPLETE: email sent (Day 5 USA wave retry)"
                safe_csv_update.safe_update(lid, new_status=new_status)
                ok += 1
                log(f"  SENT {lid} {name} -> {email}")
            else:
                log(f"  FAILED {lid} {name} -> {email}: {str(res)[:60]}")
                fail += 1
        except Exception as e:
            log(f"  ERROR {lid} {name}: {str(e)[:60]}")
            fail += 1
        time.sleep(30)  # 30s between sends
    log(f"RETRY DONE: {ok} sent, {fail} failed")

if __name__ == '__main__':
    main()
