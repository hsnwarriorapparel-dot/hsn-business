#!/usr/bin/env python3
"""Sprint email wave: all never-emailed leads EXCEPT warm conversations. Gmail-safe pacing."""
import sys, time, csv, os, tempfile
sys.path.insert(0, '/home/ubuntu')
from outreach import gmail_send
from templates import build_email

LEADS = '/home/ubuntu/leads.csv'
LOG = '/home/ubuntu/sprint_email_log.txt'

def log(m):
    line = time.strftime('%H:%M:%S') + ' ' + m
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')

def update_status(lead_id, new_status):
    with open(LEADS) as f:
        rows = list(csv.reader(f))
    idx = {h: i for i, h in enumerate(rows[0])}
    for r in rows[1:]:
        if r[0] == lead_id:
            r[idx['Status']] = (r[idx['Status']] + ' | ' + new_status)[:250]
    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='') as f:
        csv.writer(f).writerows(rows)
    with open(tmp) as f:
        assert len(list(csv.reader(f))) == len(rows)
    os.replace(tmp, LEADS)

WARM = {'L007', 'L026', 'L074', 'L078', 'L132'}

rows = list(csv.reader(open(LEADS)))
idx = {h: i for i, h in enumerate(rows[0])}
ammo = []
for r in rows[1:]:
    if r[0] in WARM:
        continue
    st = r[idx['Status']]
    if 'REPLIED' in st or 'HOT' in st:
        continue  # never cold-template a warm client
    em = (r[idx['Email']] or '').strip()
    if not em or 'email sent' in st.lower() or 'FAILED' in st:
        continue
    if '@' not in em:
        continue
    ammo.append(r)

log(f"SPRINT EMAIL WAVE: {len(ammo)} targets (warm leads excluded)")
sent = failed = 0
for r in ammo:
    lid = r[0]
    name = r[1].replace('&', 'and')
    email = r[idx['Email']].strip().lower()
    country = r[idx['Country']] or 'Europe'
    subject, body = build_email(name, f"martial arts and boxing gym in {country}")
    try:
        res = gmail_send(email, subject, body)
        ok = ('sent' in str(res).lower()) or (isinstance(res, dict) and res.get('ok'))
    except Exception as e:
        ok = False
        res = str(e)[:40]
    if ok:
        sent += 1
        update_status(lid, f"COMPLETE: email sent (sprint Day 1, {time.strftime('%Y-%m-%d')})")
        log(f"  OK {lid} {name[:20]} -> {email[:32]}")
    else:
        failed += 1
        update_status(lid, "EMAIL FAILED (sprint Day 1)")
        log(f"  FAIL {lid} {name[:20]} -> {str(res)[:40]}")
    time.sleep(38)

log(f"WAVE DONE: {sent} sent, {failed} failed")
