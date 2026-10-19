#!/usr/bin/env python3
"""Day 6 auto-pipeline: hunt to 100 -> email 100 -> WA 10 -> IG remaining."""
import sys, time, json, csv, os, tempfile, re
sys.path.insert(0, '/home/ubuntu')
from outreach import wa_send, ig_open_profile, ig_follow, ig_dm
from templates import build_wa, build_email, build_dm
from cdp_helper import get_tabs, connect

def log(m):
    line = time.strftime('%H:%M:%S') + ' ' + m
    print(line, flush=True)
    with open('/home/ubuntu/day6_log.txt', 'a') as f:
        f.write(line + '\n')

def load():
    with open('/home/ubuntu/leads.csv') as f:
        return list(csv.reader(f))

def update_status(lead_id, new_status):
    rows = load()
    idx = {h: i for i, h in enumerate(rows[0])}
    for r in rows[1:]:
        if r[0] == lead_id:
            r[idx['Status']] = (r[idx['Status']] + ' | ' + new_status)[:250]
    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='') as f:
        csv.writer(f).writerows(rows)
    with open(tmp) as f:
        assert len(list(csv.reader(f))) == len(rows)
    os.replace(tmp, '/home/ubuntu/leads.csv')

log("DAY 6 PIPELINE START")
rows = load()
idx = {h: i for i, h in enumerate(rows[0])}

# PHASE 0: count ammo
ammo = [r for r in rows[1:] if (r[idx['Email']] or '').strip()
        and 'email sent' not in r[idx['Status']].lower() and 'FAILED' not in r[idx['Status']]]
log(f"email ammo: {len(ammo)}")

# PHASE 1: email up to 100 (gmail safe pacing 30-45s)
import traceback
log(f"PHASE 1 start: {len(ammo[:100])} targets")
sent = 0
for r in ammo[:100]:
    lid = r[0]
    name = r[1].replace('&', 'and')
    email = r[idx['Email']].strip().lower()
    country = r[idx['Country']] or 'Europe'
    if '@' not in email or any(b in email for b in ['gmail.com','hotmail.com','yahoo.com']) and 'info' in email:
        pass  # allow info@ gmails from real businesses
    try:
        from googleapiclient.discovery import build
    except ImportError:
        os.system('pip install --quiet google-api-python-client google-auth-oauthlib 2>/dev/null')
    from outreach import gmail_send
    subject, body = build_email(name, f"martial arts and boxing gym in {country}")
    res = gmail_send(email, subject, body)
    ok = res.get('ok') if isinstance(res, dict) else ('sent' in str(res).lower())
    log(f"  EMAIL {lid} {name[:20]} -> {email}: {'OK' if ok else str(res)[:50]}")
    if ok:
        update_status(lid, f"COMPLETE: email sent (Day 6, {time.strftime('%Y-%m-%d')})")
        sent += 1
    else:
        update_status(lid, "EMAIL FAILED (Day 6)")
    time.sleep(38)

log(f"PHASE 1 DONE: {sent} emails")

# PHASE 2: WA to 10 best fresh candidates
rows = load()
idx = {h: i for i, h in enumerate(rows[0])}
wa_cands = [r for r in rows[1:] if (r[idx['Phone']] or '').strip() and len(r[idx['Phone']].strip()) >= 11
            and 'WA' not in r[idx['Status']]]
wa_sent = 0
for r in wa_cands[:10]:
    lid, name, phone = r[0], r[1].replace('&', 'and'), r[idx['Phone']].strip()
    country = r[idx['Country']] or 'Europe'
    try:
        res = wa_send(phone, build_wa(name, f"martial arts gym in {country}"))
        ok = '"ok":true' in str(res)
        log(f"  WA {lid} {name[:20]} -> {phone}: {'OK' if ok else 'FAIL'}")
        if ok:
            update_status(lid, "WA sent (Day 6)")
            wa_sent += 1
        time.sleep(35)
    except Exception as e:
        log(f"  WA ERR {lid}: {str(e)[:40]}")
log(f"PHASE 2 DONE: {wa_sent} WA")

# PHASE 3: IG follow+DM for leads with handles not yet IG'd
rows = load()
idx = {h: i for i, h in enumerate(rows[0])}
ig_cands = [r for r in rows[1:] if (r[idx['IG Username']] or '').strip() and 'IG' not in r[idx['Status']]]
log(f"IG candidates: {len(ig_cands)}")
ig_done = 0
for r in ig_cands[:60]:
    lid, name = r[0], r[1]
    handle = r[idx['IG Username']].strip().lstrip('@')
    try:
        ok = ig_open_profile(handle)
        if not ok:
            update_status(lid, 'IG not found')
            log(f"  NOTFOUND @{handle}")
            time.sleep(5)
            continue
        tab = [t for t in get_tabs() if f'instagram.com/{handle}' in t['url'] and t['type']=='page']
        if not tab: continue
        ws = connect(tab[-1])
        fr = ig_follow(ws)
        time.sleep(3)
        dm = ig_dm(ws, build_dm(name, "martial arts training business"))
        ws.close()
        update_status(lid, f'IG follow={fr} dm={dm} (Day 6)')
        ig_done += 1
        log(f"  IG OK {name[:18]} @{handle}")
        time.sleep(22)
    except Exception as e:
        log(f"  IG ERR {lid}: {str(e)[:40]}")
        time.sleep(8)
log(f"PHASE 3 DONE: {ig_done} IG")
log("DAY 6 PIPELINE COMPLETE")
