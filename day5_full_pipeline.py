#!/usr/bin/env python3
"""Day 5 full pipeline: 10 WA sends (best EU leads) + 50 IG follow/DM (USA leads)."""
import sys, time, json, csv, os, tempfile
sys.path.insert(0, '/home/ubuntu')
from outreach import wa_send, ig_open_profile, ig_follow, ig_dm
from templates import build_wa, build_dm
from cdp_helper import get_tabs, connect

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
    with open(tmp) as f:
        check = list(csv.reader(f))
    assert len(check) == len(rows)
    os.replace(tmp, '/home/ubuntu/leads.csv')

def log(m):
    line = time.strftime('%H:%M:%S') + ' ' + m
    print(line, flush=True)
    with open('/home/ubuntu/day5_full_log.txt', 'a') as f:
        f.write(line + "\n")

rows = list(csv.reader(open('/home/ubuntu/leads.csv')))
idx = {h: i for i, h in enumerate(rows[0])}

# PHASE 1: 10 WA sends
log("PHASE 1: WA to 10 best leads")
wa_ids = json.load(open('/tmp/wa_today_10.json'))
by_id = {r[0]: r for r in rows[1:]}
wa_sent = 0
for lid in wa_ids:
    r = by_id[lid]
    name = r[1].replace('&', 'and')
    phone = r[idx['Phone']].strip()
    country = r[idx['Country']] or 'Europe'
    detail = f"martial arts gym in {country}"
    msg = build_wa(name, detail)
    res = wa_send(phone, msg)
    ok = '"ok":true' in str(res)
    log(f"  WA {lid} {name[:20]} -> {phone}: {'OK' if ok else str(res)[:40]}")
    if ok:
        update_status(lid, 'WA sent (Day 5 wave)')
        wa_sent += 1
    time.sleep(35)
log(f"PHASE 1 DONE: {wa_sent}/10 WA sent")

# PHASE 2: IG follow + DM x50
log("PHASE 2: IG follow+DM x50 USA")
usa = [r for r in rows[1:] if 'Day 5 USA' in r[14] and (r[idx['IG Username']] or '').strip()]
ig_targets = [r for r in usa if 'IG' not in r[idx['Status']]][:50]
log(f"IG targets: {len(ig_targets)}")
ig_done = 0
for r in ig_targets:
    lid, name = r[0], r[1]
    handle = r[idx['IG Username']].strip().lstrip('@')
    try:
        ok = ig_open_profile(handle)
        if not ok:
            update_status(lid, 'IG not found')
            log(f"  NOTFOUND {name[:18]} @{handle}")
            time.sleep(6)
            continue
        tab = [t for t in get_tabs() if f'instagram.com/{handle}' in t['url'] and t['type']=='page']
        if not tab:
            continue
        ws = connect(tab[-1])
        fr = ig_follow(ws)
        time.sleep(3)
        dm = ig_dm(ws, build_dm(name, "martial arts training business in the USA"))
        ws.close()
        update_status(lid, f'IG follow={fr} dm={dm}')
        ig_done += 1
        log(f"  OK {name[:18]} @{handle} follow={fr} dm={dm}")
        time.sleep(22)
    except Exception as e:
        log(f"  ERR {name[:18]}: {str(e)[:40]}")
        time.sleep(8)
log(f"PHASE 2 DONE: {ig_done}/50 IG followed+DM'd")
log("ALL PHASES COMPLETE")
