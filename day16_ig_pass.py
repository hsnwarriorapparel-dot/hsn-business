#!/usr/bin/env python3
"""Day-13 (2026-10-27) IG follow + DM pass.

Same resumable pattern as the email wave: reads the CSV fresh, skips any
handle already touched, follows + DMs the profile, then marks the lead
immediately (row-targeted atomic write). Only ONE IG profile tab is used.
"""
import sys, os, time, csv, tempfile, json, re
sys.path.insert(0, '/home/ubuntu')
from outreach import ig_open_profile, ig_follow, ig_dm
from templates import build_dm
from cdp_helper import get_tabs, connect, js_eval

CSV = '/home/ubuntu/leads.csv'
LOG = '/home/ubuntu/day16_ig_log.txt'
DAY = 'Daily 2026-10-30'
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 80

JUNK_IG = ['squarespace', 'wix', 'jiujitsudotcom', 'embed', 'instagram', 'facebook',
           'wordpress', 'google', 'youtube', 'mail.', 'tiptoe', 'gymshark', 'invites']
IG_DONE = ['ig follow', 'follow=', 'followed', 'dm=', 'dm sent', 'ig dm', 'ig not found',
           'notfound', 'profile-not-found', 'ig=', 'ig profile not found',
           'ig handle mismatch']
FED = ['federation', 'verband', 'association', 'bonds', 'federal', 'excluded']
PERSONAL = ['sayyam', 'shamas', 'afzal', 'chacho nadeem']


def log(m):
    line = time.strftime('%H:%M:%S') + ' ' + m
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')


def load():
    with open(CSV, newline='', encoding='utf-8-sig') as f:
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
wave_ids = set(l.strip() for l in open('/home/ubuntu/day16_wave.txt') if l.strip())
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
    # ORDER: today's wave leads first, then leads HUNTED TODAY (same-day rule:
    # every lead found today gets IG follow+DM today), then the older backlog.
    fresh = 0 if r[0] in wave_ids else (1 if '2026-10-30' in st else 2)
    cands.append((fresh, r[0], (r[iN] or '').strip(), h, (r[iC] or '').strip()))
cands.sort()
cands = cands[:LIMIT]
log(f"IG PASS START: {len(cands)} candidates (wave {sum(1 for c in cands if c[0]==0)})")

done = notfound = errs = 0
for _, lid, name, h, country in cands:
    try:
        ok = ig_open_profile(h)
        if not ok:
            update_status(lid, f'IG profile not found ({DAY})')
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
        # IDENTITY CHECK: confirm the loaded profile is actually this lead's
        # business before following/DMing. A scraped handle can belong to a
        # different account (link-rot, a shared agency page, a script asset).
        # DMing the wrong business is a cross-send mistake -- never send blind.
        prof = json.loads(js_eval(ws, """(() => {
            const h = document.querySelector('header');
            const txt = document.body ? document.body.innerText : '';
            // header innerText line 0 = username, line 1 = display name
            let lines = h ? (h.innerText||'').split('\\n').map(s => s.trim()).filter(Boolean) : [];
            const display = lines[1] || lines[0] || '';
            const bio = (document.querySelector('header + div, header ~ div') || {}).innerText || '';
            const notFound = /Page Not Found|Sorry, this page/i.test(txt);
            return JSON.stringify({name: display.slice(0,60), desc: bio.slice(0,200), notFound: notFound});
        })()""", await_promise=False) or '{}')
        hname = (prof.get('name') or '').lower()
        hdesc = (prof.get('desc') or '').lower()
        want = (name + ' ' + country).lower()

        def strip_accents(s):
            import unicodedata
            return ''.join(c for c in unicodedata.normalize('NFKD', s)
                           if not unicodedata.combining(c))

        def tokset(s):
            s = strip_accents(s).lower()
            return {w for w in re.split(r'[^a-z0-9]+', s) if len(w) >= 4}

        wtok = tokset(want)
        htok = tokset(hname + ' ' + hdesc)
        # the handle itself is also evidence (e.g. "usmetro_bizot" vs "Us Metro")
        htok |= tokset(h.replace('_', ' ').replace('.', ' ').replace('-', ' '))
        if prof.get('notFound'):
            update_status(lid, f'IG profile not found ({DAY})')
            log(f"  NOTFOUND {lid} @{h}")
            notfound += 1
            ws.close()
            time.sleep(5)
            continue
        if wtok and not (wtok & htok):
            update_status(lid, f'IG handle mismatch, not contacted ({DAY})')
            log(f"  MISMATCH {lid} @{h} profile='{hname[:30]}' lead='{name[:24]}' - SKIPPED")
            notfound += 1
            ws.close()
            time.sleep(6)
            continue
        fr = ig_follow(ws)
        time.sleep(3)
        dm = ig_dm(ws, build_dm(name, f"martial arts training business in {country}" if country else "martial arts training business"))
        ws.close()
        update_status(lid, f'IG follow={fr} dm={dm} ({DAY})')
        done += 1
        log(f"  IG OK {name[:22]} @{h} follow={fr} dm={dm} prof='{hname[:22]}'")
        time.sleep(22)
    except Exception as e:
        log(f"  IG ERR {lid} @{h}: {str(e)[:60]}")
        errs += 1
        time.sleep(8)
log(f"IG PASS DONE: {done} follow+DM, {notfound} not found, {errs} errors")
