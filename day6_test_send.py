#!/usr/bin/env python3
"""Test one gmail send + update status if OK."""
import sys, time, csv, os, tempfile
sys.path.insert(0, '/home/ubuntu')
from outreach import gmail_send
from templates import build_email

def update_status(lead_id, new_status):
    with open('/home/ubuntu/leads.csv') as f:
        rows = list(csv.reader(f))
    idx = {h: i for i, h in enumerate(rows[0])}
    for r in rows[1:]:
        if r[0] == lead_id:
            r[idx['Status']] = (r[idx['Status']] + ' | ' + new_status)[:250]
    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='') as f:
        csv.writer(f).writerows(rows)
    os.replace(tmp, '/home/ubuntu/leads.csv')

rows = list(csv.reader(open('/home/ubuntu/leads.csv')))
idx = {h: i for i, h in enumerate(rows[0])}
ammo = [r for r in rows[1:] if (r[idx['Email']] or '').strip()
        and 'email sent' not in r[idx['Status']].lower() and 'FAILED' not in r[idx['Status']]]
r = ammo[0]
name = r[1].replace('&', 'and')
email = r[idx['Email']].strip().lower()
country = r[idx['Country']] or 'Europe'
print(f"TEST SEND: {r[0]} {name} -> {email}")
subject, body = build_email(name, f"martial arts and boxing gym in {country}")
res = gmail_send(email, subject, body)
print("RESULT:", str(res)[:120])
if isinstance(res, dict) and res.get('ok'):
    update_status(r[0], f"COMPLETE: email sent (Day 6 test, {time.strftime('%Y-%m-%d')})")
    print("status updated")
