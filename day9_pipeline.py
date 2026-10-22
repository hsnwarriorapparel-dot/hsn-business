#!/usr/bin/env python3
"""Day 9 auto-pipeline (2026-10-21): email up to 100 ammo leads (38s Gmail-safe),
10 WA to MOBILE-PREFIX-ONLY fresh candidates (landline hole fixed),
IG follow+DM for never-IG'd leads. Resumable: every send marks the CSV immediately."""
import sys, time, csv, os, tempfile, re
sys.path.insert(0, '/home/ubuntu')
from outreach import wa_send, ig_open_profile, ig_follow, ig_dm, gmail_send
from templates import build_wa, build_email, build_dm
from cdp_helper import get_tabs, connect

CSV = '/home/ubuntu/leads.csv'
LOG = '/home/ubuntu/day9_log.txt'
DAY = 'Day 9'
DATE = '2026-10-21'
MAX_EMAILS = int(sys.argv[1]) if len(sys.argv) > 1 else 100
MAX_WA = int(sys.argv[2]) if len(sys.argv) > 2 else 10

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
        if r[0] == lead_id:
            r[idx['Status']] = (r[idx['Status']].rstrip(' |') + ' | ' + new_status)[:250]
    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(rows)
    os.replace(tmp, CSV)

# ---- hardened "already contacted" markers (case-insensitive) ----
WA_DONE = ['whatsapp sent', 'wa sent', 'wa=', '"ok":true', 'not on whatsapp',
           "isn't on whatsapp", 'no-composer', 'wa err', 'wa failed', 'wa-pending',
           'whatsapp-only', 'wa numbers banked', 'wa-not']
IG_DONE = ['ig follow', 'follow=', 'followed', 'dm=', 'dm sent', 'ig dm', 'ig not found',
           'notfound', 'profile-not-found', 'ig=', 'ig profile not found']
ACTIVE  = ['follow-up', 'hot lead', 'negotiat', 'sample quote', 'awaiting', 'replied']
FED     = ['federation', 'verband', 'association', 'bonds', 'federal', 'excluded']
JUNK_IG = ['squarespace', 'wix', 'jiujitsudotcom', 'embed', 'instagram', 'facebook',
           'wordpress', 'google', 'youtube', 'mail.', 'tiptoe', 'gymshark']
PERSONAL = ['sayyam', 'shamas', 'afzal', 'chacho nadeem']

# country -> MOBILE prefixes only (landlines are never on WhatsApp; USA = email-first, no WA)
MOBILE_PREFIX = {
    'UK': ['447'], 'Spain': ['346', '347'], 'Portugal': ['3519'],
    'Italy': ['393'], 'Ireland': ['3538'], 'Netherlands': ['316'],
    'Germany': ['4915', '4916', '4917'], 'France': ['336', '337'],
}
PREFIX = {'Spain': ['34'], 'Portugal': ['351'], 'Italy': ['39'], 'France': ['33'],
          'UK': ['44'], 'Germany': ['49'], 'Switzerland': ['41'], 'Netherlands': ['31'],
          'Ireland': ['353'], 'Belgium': ['32'], 'Austria': ['43'], 'Sweden': ['46'],
          'Denmark': ['45'], 'Norway': ['47'], 'Finland': ['358'], 'Poland': ['48'],
          'Czech Republic': ['420'], 'Hungary': ['36'], 'Greece': ['30'], 'USA': ['1']}

def valid_email(e):
    e = re.sub(r'^(%20|u00a0|\s)+', '', (e or '').strip().lower())
    return bool(re.match(r'^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$', e)) and 'http' not in e

def norm_phone(p, country):
    p = re.sub(r'[^\d+]', '', (p or '').strip())
    if not p:
        return ''
    if p.startswith('0'):          # UK local format
        p = '44' + p[1:]
    if not p.startswith('+'):
        p = '+' + p
    d = re.sub(r'\D', '', p)
    if len(d) < 11 or '*' in (p or ''):
        return ''
    pref = PREFIX.get(country)
    if pref and not any(d.startswith(x) for x in pref):
        return ''
    return p

def is_mobile(p, country):
    d = re.sub(r'\D', '', p)
    mob = MOBILE_PREFIX.get(country)
    if not mob:                     # USA etc: skip WA entirely
        return False
    return any(d.startswith(x) for x in mob)

log(f"{DAY} PIPELINE START (emails target {MAX_EMAILS}, WA target {MAX_WA})")
rows = load()
idx = {h: i for i, h in enumerate(rows[0])}
iE, iP, iIG, iS, iC, iN = (idx['Email'], idx['Phone'], idx['IG Username'],
                           idx['Status'], idx['Country'], idx['Name'])

# ---------------- PHASE 1: EMAIL WAVE ----------------
ammo = []
for r in rows[1:]:
    st = (r[iS] or '').lower()
    if not (r[iE] or '').strip():
        continue
    if 'email sent' in st or 'failed' in st or 're-hunt' in st or 'excluded' in st:
        continue
    if any(m in st for m in ACTIVE):
        continue
    if not valid_email(r[iE]):
        update_status(r[0], 'EXCLUDED (Day 9): invalid email format')
        continue
    ammo.append(r)
log(f"email ammo: {len(ammo)}")
sent = failed = 0
for r in ammo[:MAX_EMAILS]:
    lid, name = r[0], r[iN].replace('&', 'and')
    email = r[iE].strip().lower()
    country = r[iC] or 'Europe'
    region = 'USA' if country == 'USA' else 'Europe'
    try:
        subject, body = build_email(name, f"martial arts and boxing gym in {country}", region=region)
        res = gmail_send(email, subject, body)
        ok = res.get('ok') if isinstance(res, dict) else ('sent' in str(res).lower())
        log(f"  EMAIL {lid} {name[:22]} -> {email}: {'OK' if ok else str(res)[:50]}")
        if ok:
            update_status(lid, f"COMPLETE: email sent ({DAY}, {DATE})")
            sent += 1
        else:
            update_status(lid, f"EMAIL FAILED ({DAY}): {str(res)[:40]}")
            failed += 1
    except Exception as e:
        log(f"  EMAIL ERR {lid}: {str(e)[:60]}")
        update_status(lid, f"EMAIL FAILED ({DAY}): exception")
        failed += 1
    time.sleep(38)
log(f"PHASE 1 DONE: {sent} sent, {failed} failed")

# ---------------- PHASE 2: WA WAVE (max 10, MOBILE ONLY, fresh first) ----------------
rows = load()
cands = []
for r in rows[1:]:
    st = (r[iS] or '').lower()
    name_l = r[iN].lower()
    if any(p in name_l for p in PERSONAL):
        continue
    if any(m in st for m in WA_DONE):
        continue
    if any(m in st for m in ACTIVE):
        continue
    if any(m in st for m in FED):
        continue
    ph = norm_phone(r[iP], r[iC])
    if not ph or not is_mobile(ph, r[iC]):
        continue
    fresh = ('day 8' in st or 'day 9' in st or 'gmaps' in st)
    cands.append((0 if fresh else 1, r[0], r[iN].replace('&', 'and'), ph, r[iC] or 'Europe'))
cands.sort(key=lambda x: x[0])
cands = cands[:MAX_WA]
log(f"WA candidates selected: {len(cands)}")
wa_sent = 0
for _, lid, name, ph, country in cands:
    try:
        res = wa_send(ph, build_wa(name, f"martial arts gym in {country}"))
        ok = '"ok":true' in str(res)
        log(f"  WA {lid} {name[:20]} -> {ph}: {'OK' if ok else str(res)[:60]}")
        if ok:
            update_status(lid, f"WA sent ({DAY}) - verified transcript")
            wa_sent += 1
        else:
            update_status(lid, f"WA FAILED ({DAY}): {str(res)[:40]}")
        time.sleep(35)
    except Exception as e:
        log(f"  WA ERR {lid}: {str(e)[:50]}")
log(f"PHASE 2 DONE: {wa_sent} WA")

# ---------------- PHASE 3: IG FOLLOW + DM WAVE ----------------
rows = load()
ig_cands = []
for r in rows[1:]:
    st = (r[iS] or '').lower()
    h = (r[iIG] or '').strip().lstrip('@')
    if not h or h.lower() in JUNK_IG:
        continue
    if any(m in st for m in IG_DONE):
        continue
    if any(m in st for m in FED):
        continue
    fresh = 'day 9' in st or 'gmaps' in st
    ig_cands.append((0 if fresh else 1, r[0], r[iN], h))
ig_cands.sort(key=lambda x: x[0])
ig_cands = ig_cands[:60]
log(f"IG candidates selected: {len(ig_cands)} (fresh: {sum(1 for c in ig_cands if c[0]==0)})")
ig_done = 0
for _, lid, name, h in ig_cands:
    try:
        ok = ig_open_profile(h)
        if not ok:
            update_status(lid, f'IG profile not found ({DAY} retry)')
            log(f"  NOTFOUND @{h}")
            time.sleep(5)
            continue
        tab = [t for t in get_tabs() if f'instagram.com/{h}' in t['url'] and t['type'] == 'page']
        if not tab:
            log(f"  IG ERR {lid}: no tab for @{h}")
            continue
        ws = connect(tab[-1])
        fr = ig_follow(ws)
        time.sleep(3)
        dm = ig_dm(ws, build_dm(name, "martial arts training business"))
        ws.close()
        update_status(lid, f'IG follow={fr} dm={dm} ({DAY})')
        ig_done += 1
        log(f"  IG OK {name[:18]} @{h} follow={fr} dm={dm}")
        time.sleep(22)
    except Exception as e:
        log(f"  IG ERR {lid}: {str(e)[:40]}")
        time.sleep(8)
log(f"PHASE 3 DONE: {ig_done} IG follow+DM")
log(f"{DAY} PIPELINE COMPLETE")
