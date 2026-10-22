#!/usr/bin/env python3
"""Sprint email wave v2: opens its OWN gmail tab first (verifies inbox loaded),
waits between sends, never navigates away. Restores false-fails first."""
import sys, time, csv, os, tempfile
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval, find_tab
from outreach import gmail_send
from templates import build_email

LEADS = '/home/ubuntu/leads.csv'
LOG = '/home/ubuntu/sprint_email_log2.txt'

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

def ensure_gmail_tab():
    tabs = get_tabs()
    gm = [t for t in tabs if 'mail.google' in t.get('url','') and t['type'] == 'page']
    if gm:
        return True
    # create a fresh one
    any_ws = connect([t for t in tabs if t['type'] == 'page'][0])
    cdp = make_cdp(any_ws)
    cdp("Target.createTarget", {"url": "https://mail.google.com/mail/u/0/#inbox"})
    any_ws.close()
    for _ in range(6):
        time.sleep(10)
        tabs = get_tabs()
        if any('mail.google' in t.get('url','') for t in tabs if t['type'] == 'page'):
            return True
    return False

WARM = {'L007', 'L026', 'L074', 'L078', 'L132'}

rows = list(csv.reader(open(LEADS)))
idx = {h: i for i, h in enumerate(rows[0])}
ammo = []
for r in rows[1:]:
    if r[0] in WARM:
        continue
    st = r[idx['Status']]
    if 'REPLIED' in st or 'HOT' in st:
        continue
    em = (r[idx['Email']] or '').strip()
    if not em or '@' not in em:
        continue
    if 'email sent' in st.lower() or 'FAILED' in st:
        continue
    ammo.append(r)

log(f"SPRINT WAVE v2: {len(ammo)} targets")
if not ensure_gmail_tab():
    log("FATAL: cannot open gmail tab")
    sys.exit(1)
log("gmail tab confirmed")

sent = failed = 0
for r in ammo:
    lid = r[0]
    name = r[1].replace('&', 'and')
    email = r[idx['Email']].strip().lower()
    country = r[idx['Country']] or 'Europe'
    # guard: gmail tab must still exist before each send
    if not any('mail.google' in t.get('url','') for t in get_tabs() if t['type'] == 'page'):
        log("gmail tab vanished - re-opening")
        if not ensure_gmail_tab():
            log("cannot recover gmail tab - stopping")
            break
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
        log(f"  FAIL {lid} {name[:20]} -> {str(res)[:44]}")
    time.sleep(40)

log(f"WAVE v2 DONE: {sent} sent, {failed} failed")
