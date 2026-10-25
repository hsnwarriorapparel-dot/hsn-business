#!/usr/bin/env python3
"""Day-11 IG follow + DM pass over the leads that still need it.
Reads the CSV fresh, picks never-IG'd handles, follows, DMs, and marks the
lead's status immediately after each profile. Resumable (skips anything already
marked). Skips federation / junk handles and personal contacts."""
import sys, os, time, csv, tempfile
sys.path.insert(0, '/home/ubuntu')
from outreach import ig_open_profile, ig_follow, ig_dm
from templates import build_dm
from cdp_helper import get_tabs, connect

CSV = '/home/ubuntu/leads.csv'
LOG = '/home/ubuntu/day11_ig_log.txt'
DAY = 'Daily 2026-10-25'
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 60

JUNK_IG = ['squarespace', 'wix', 'jiujitsudotcom', 'embed', 'instagram', 'facebook',
           'wordpress', 'google', 'youtube', 'mail.', 'tiptoe', 'gymshark', 'invites']
IG_DONE = ['ig follow', 'follow=', 'followed', 'dm=', 'dm sent', 'ig dm', 'ig not found',
           'notfound', 'profile-not-found', 'ig=', 'ig profile not found']
FED = ['federation', 'verband', 'association', 'bonds', 'federal', 'excluded']
PERSONAL = ['sayyam', 'shamas', 'afzal', 'chacho nadeem']


def log(m):
    line = time.strftime('%H:%M:%S') + ' ' + m
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')


def load():
    with open(CSV, newline='', encoding='utf-8') as f:
        return list(csv.reader(f))


def update_status(lead_id, new_status):
    rows = load()
    idx = {h: i for i, h in enumerate(rows[0])}
    for r in rows[1:]:
        if r and r[0] == lead_id:
            r[idx['Status']] = (r[idx['Status']].rstrip(' |') + ' | ' + new_status)[:250]
    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(rows)
    os.replace(tmp, CSV)


rows = load()
idx = {h: i for i, h in enumerate(rows[0])}
iIG, iS, iN, iC = idx['IG Username'], idx['Status'], idx['Name'], idx['Country']
cands = []
for r in rows[1:]:
    if len(r) <= iS:
        continue
    st = (r[iS] or '').lower()
    h = (r[iIG] or '').strip().lstrip('@')
    if not h or h.lower() in JUNK_IG:
        continue
    if any(m in st for m in IG_DONE):
        continue
    if any(m in st for m in FED):
        continue
    if any(p in (r[iN] or '').lower() for p in PERSONAL):
        continue
    fresh = 'gmaps' in st or 'daily' in st or '2026-10-2' in st
    cands.append((0 if fresh else 1, r[0], (r[iN] or '').strip(), h, (r[iC] or '').strip()))
cands.sort(key=lambda x: x[0])
cands = cands[:LIMIT]
log(f"IG PASS START: {len(cands)} candidates (fresh {sum(1 for c in cands if c[0]==0)})")

done = notfound = errs = 0
for _, lid, name, h, country in cands:
    try:
        ok = ig_open_profile(h)
        if not ok:
            update_status(lid, 'IG profile not found (2026-10-25)')
            log(f"  NOTFOUND {lid} @{h}")
            notfound += 1
            time.sleep(5)
            continue
        tabs = [t for t in get_tabs() if f'instagram.com/{h}' in t['url'] and t['type'] == 'page']
        if not tabs:
            log(f"  IG ERR {lid}: no tab for @{h}")
            errs += 1
            time.sleep(8)
            continue
        ws = connect(tabs[-1])
        fr = ig_follow(ws)
        time.sleep(3)
        dm = ig_dm(ws, build_dm(name, f"martial arts training business in {country}" if country else "martial arts training business"))
        ws.close()
        update_status(lid, f'IG follow={fr} dm={dm} ({DAY})')
        done += 1
        log(f"  IG OK {name[:22]} @{h} follow={fr} dm={dm}")
        time.sleep(22)
    except Exception as e:
        log(f"  IG ERR {lid} @{h}: {str(e)[:60]}")
        errs += 1
        time.sleep(8)
log(f"IG PASS DONE: {done} follow+DM, {notfound} not found, {errs} errors")
