#!/usr/bin/env python3
"""Dry-run: replicate day9_pipeline selection filters, print targets without sending."""
import csv, re

CSV = '/home/ubuntu/leads.csv'
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
MOBILE_PREFIX = {'UK': ['447'], 'Spain': ['346', '347'], 'Portugal': ['3519'],
                 'Italy': ['393'], 'Ireland': ['3538'], 'Netherlands': ['316'],
                 'Germany': ['4915', '4916', '4917'], 'France': ['336', '337']}
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
    if not p: return ''
    if p.startswith('0'): p = '44' + p[1:]
    if not p.startswith('+'): p = '+' + p
    d = re.sub(r'\D', '', p)
    if len(d) < 11: return ''
    pref = PREFIX.get(country)
    if pref and not any(d.startswith(x) for x in pref): return ''
    return p

def is_mobile(p, country):
    d = re.sub(r'\D', '', p)
    mob = MOBILE_PREFIX.get(country)
    if not mob: return False
    return any(d.startswith(x) for x in mob)

rows = list(csv.reader(open(CSV, newline='', encoding='utf-8')))
idx = {h: i for i, h in enumerate(rows[0])}
iE, iP, iIG, iS, iC, iN = (idx['Email'], idx['Phone'], idx['IG Username'],
                           idx['Status'], idx['Country'], idx['Name'])

ammo = []
for r in rows[1:]:
    st = (r[iS] or '').lower()
    if not (r[iE] or '').strip(): continue
    if 'email sent' in st or 'failed' in st or 're-hunt' in st or 'excluded' in st: continue
    if any(m in st for m in ACTIVE): continue
    if not valid_email(r[iE]): continue
    ammo.append(r)
print(f"EMAIL ammo: {len(ammo)} -> sending first 100")
print("first 3:", [(r[0], r[iN][:20]) for r in ammo[:3]])
print("last 3 of wave:", [(r[0], r[iN][:20]) for r in ammo[97:100]])

cands = []
for r in rows[1:]:
    st = (r[iS] or '').lower()
    if any(p in r[iN].lower() for p in PERSONAL): continue
    if any(m in st for m in WA_DONE): continue
    if any(m in st for m in ACTIVE): continue
    if any(m in st for m in FED): continue
    ph = norm_phone(r[iP], r[iC])
    if not ph or not is_mobile(ph, r[iC]): continue
    fresh = ('day 8' in st or 'day 9' in st or 'gmaps' in st)
    cands.append((0 if fresh else 1, r[0], r[iN], ph, r[iC]))
cands.sort(key=lambda x: x[0])
sel = cands[:10]
print(f"\nWA pool: {len(cands)} (fresh-first) -> selecting 10")
for c in sel:
    print(f"  {c[1]} | {c[2][:30]:30} | {c[3]} | {c[4]}")
landlines_in_pool = [c for c in cands if not is_mobile(c[3], c[4])]
print("landlines leaked into pool:", len(landlines_in_pool))
for r in rows[1:]:
    if r[0] in ('L078','L132','L026'):
        print(f"  active-client guard: {r[0]} in WA pool? {'YES - BUG' if any(c[1]==r[0] for c in cands) else 'no (correct)'}")

ig = []
for r in rows[1:]:
    st = (r[iS] or '').lower()
    h = (r[iIG] or '').strip().lstrip('@')
    if not h or h.lower() in JUNK_IG: continue
    if any(m in st for m in IG_DONE): continue
    if any(m in st for m in FED): continue
    ig.append((r[0], r[iN][:20], h))
print(f"\nIG candidates: {len(ig)}")
for c in ig[:10]:
    print(f"  {c[0]} | {c[1]} | @{c[2]}")
