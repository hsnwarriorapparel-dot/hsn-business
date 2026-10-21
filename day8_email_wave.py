#!/usr/bin/env python3
"""Day 8 email wave (catch-up): send to fresh Day-8 ammo only.
Row-targeted status writes via safe_csv_update. 38s Gmail-safe pacing.
Max 100 (daily quota). No WA/IG here — those ran separately."""
import sys, time, csv
sys.path.insert(0, '/home/ubuntu')
from outreach import gmail_send
from templates import build_email
from safe_csv_update import safe_update

CSV = '/home/ubuntu/leads.csv'
LOG = '/home/ubuntu/day8_email_log.txt'
MAX = 100

def log(m):
    line = f"{time.strftime('%H:%M:%S')} {m}"
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + "\n")

def load():
    with open(CSV, newline='', encoding='utf-8') as f:
        return list(csv.reader(f))

ACTIVE = ['follow-up', 'hot lead', 'negotiat', 'sample quote', 'awaiting']

rows = load()
idx = {h: i for i, h in enumerate(rows[0])}
iE, iS, iC, iN = idx['Email'], idx['Status'], idx['Country'], idx['Name']

ammo = []
for r in rows[1:]:
    st = (r[iS] or '').lower()
    if 'day 8' not in st and 'day 8' not in (r[idx['Notes']] or '').lower():
        continue
    if not (r[iE] or '').strip():
        continue
    if 'email sent' in st or 'failed' in st:
        continue
    if any(m in st for m in ACTIVE):
        continue
    ammo.append(r)

log(f"DAY 8 EMAIL WAVE START: {len(ammo)} Day-8 ammo, sending max {MAX}")
sent = failed = 0
for r in ammo[:MAX]:
    lid, name = r[0], r[iN].replace('&', 'and')
    email = r[iE].strip().lower()
    country = r[iC] or 'Europe'
    region = 'USA' if country == 'USA' else 'Europe'
    try:
        subject, body = build_email(name, f"martial arts and boxing gym in {country}", region=region)
        res = gmail_send(email, subject, body)
        ok = res.get('ok') if isinstance(res, dict) else ('sent' in str(res).lower())
        if ok:
            safe_update(lid, append_status="COMPLETE: email sent (Day 8 wave, 2026-10-21)")
            sent += 1
            log(f"  EMAIL {lid} {name[:22]} -> {email}: OK")
        else:
            safe_update(lid, append_status=f"EMAIL FAILED (Day 8 wave): {str(res)[:40]}")
            failed += 1
            log(f"  EMAIL {lid} {name[:22]} -> {email}: {str(res)[:50]}")
    except Exception as e:
        safe_update(lid, append_status="EMAIL FAILED (Day 8 wave): exception")
        failed += 1
        log(f"  EMAIL ERR {lid}: {str(e)[:60]}")
    time.sleep(38)

log(f"DAY 8 EMAIL WAVE DONE: {sent} sent, {failed} failed")
