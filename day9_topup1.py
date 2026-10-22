#!/usr/bin/env python3
"""Top-up: 1 email to next unsent valid ammo lead (L809). Reaches tonight's 100 quota."""
import sys, csv, re, time
sys.path.insert(0, '/home/ubuntu')
from outreach import gmail_send
from templates import build_email

CSV = '/home/ubuntu/leads.csv'
rows = list(csv.reader(open(CSV, newline='', encoding='utf-8')))
idx = {h: i for i, h in enumerate(rows[0])}
iE, iS, iC, iN = idx['Email'], idx['Status'], idx['Country'], idx['Name']
ACTIVE = ['follow-up', 'hot lead', 'negotiat', 'sample quote', 'awaiting', 'replied']

def valid_email(e):
    e = re.sub(r'^(%20|u00a0|\s)+', '', (e or '').strip().lower())
    return bool(re.match(r'^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$', e)) and 'http' not in e

target = None
for r in rows[1:]:
    st = (r[iS] or '').lower()
    if not (r[iE] or '').strip(): continue
    if 'email sent' in st or 'failed' in st or 're-hunt' in st or 'excluded' in st: continue
    if any(m in st for m in ACTIVE): continue
    if not valid_email(r[iE]): continue
    if not r[0].startswith('L8'): continue   # next after tonight's L693-L806 wave
    target = r
    break

if not target:
    print("NO TARGET FOUND")
    sys.exit(1)
lid, name = target[0], target[iN].replace('&', 'and')
email = target[iE].strip().lower()
country = target[iC] or 'Europe'
print(f"target: {lid} | {name} | {email} | {country}")
subject, body = build_email(name, f"martial arts and boxing gym in {country}", region='Europe')
res = gmail_send(email, subject, body)
ok = res.get('ok') if isinstance(res, dict) else ('sent' in str(res).lower())
print("send:", "OK" if ok else str(res)[:80])
if ok:
    import tempfile, os
    rows = list(csv.reader(open(CSV, newline='', encoding='utf-8')))
    idx = {h: i for i, h in enumerate(rows[0])}
    for r in rows[1:]:
        if r[0] == lid:
            r[idx['Status']] = (r[idx['Status']].rstrip(' |') + ' | ' + f"COMPLETE: email sent (Day 9, 2026-10-21)")[:250]
    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(rows)
    os.replace(tmp, CSV)
    # read-back
    rows2 = list(csv.reader(open(CSV, newline='', encoding='utf-8')))
    got = [r[0] for r in rows2[1:] if r[0] == lid and 'email sent (Day 9' in r[idx['Status']]]
    print("marked+verified:", got)
