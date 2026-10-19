#!/usr/bin/env python3
"""Day 7 foreground test send: ONE real email, print raw gmail_send return."""
import sys, csv
sys.path.insert(0, '/home/ubuntu')
from outreach import gmail_send
from templates import build_email

with open('/home/ubuntu/leads.csv', newline='', encoding='utf-8') as f:
    rows = list(csv.reader(f))

# pick first ammo lead (email, no 'email sent', no 'failed')
target = None
for r in rows[1:]:
    st = r[11].lower()
    if r[9].strip() and 'email sent' not in st and 'failed' not in st and 're-hunt' not in st:
        target = r
        break
assert target, 'no ammo!'
lid, name, email, country = target[0], target[1].replace('&', 'and'), target[9].strip().lower(), target[6] or 'Europe'
print(f"TEST SEND -> {lid} | {name} | {email} | {country}")
subject, body = build_email(name, f"martial arts and boxing gym in {country}", region='Europe')
print("SUBJECT:", subject)
res = gmail_send(email, subject, body)
print("RAW RETURN:", repr(res))
print("TYPE:", type(res))
