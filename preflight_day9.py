#!/usr/bin/env python3
"""Day-9 pre-flight: ammo quality, active-client exclusion, WA mobile candidates, IG candidates."""
import csv, re
from collections import Counter

rows = list(csv.reader(open('/home/ubuntu/leads.csv', encoding='utf-8', errors='replace')))
idx = {h: i for i, h in enumerate(rows[0])}

def valid_email(e):
    e = re.sub(r'^(%20|u00a0|\s)+', '', (e or '').strip().lower())
    return bool(re.match(r'^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$', e)) and 'http' not in e

def norm_email(e):
    return re.sub(r'^(%20|u00a0|\s)+', '', (e or '').strip().lower())

ACTIVE = ['brazilian fight', 'duramuk', 'scorpion boxing', 'lucero', 'alvaro', 'campeao']

ammo = []
for r in rows[1:]:
    if len(r) < 12: continue
    email = (r[idx['Email']] or '').strip()
    status = (r[idx['Status']] or '').strip()
    if not email: continue
    if 'email sent' in status.lower() or 'FAILED' in status: continue
    ammo.append(r)

valid = [r for r in ammo if valid_email(r[idx['Email']])]
invalid = [r for r in ammo if not valid_email(r[idx['Email']])]
print("ammo raw:", len(ammo), "| valid:", len(valid), "| invalid:", len(invalid))
print("invalid examples:", [(r[0], r[idx['Email']][:45]) for r in invalid[:10]])

active_in = [r for r in valid if any(a in r[1].lower() for a in ACTIVE)]
print("ACTIVE CLIENTS in valid ammo:", [(r[0], r[1][:25]) for r in active_in])

wave = [r for r in valid if not any(a in r[1].lower() for a in ACTIVE)][:100]
print("WAVE SIZE:", len(wave))
print("wave countries:", dict(Counter((r[idx['Country']] or '?').strip() or '?' for r in wave)))
print("wave first 5:", [(r[0], r[1][:22], r[idx['Email']][:32]) for r in wave[:5]])
print("wave last 3:", [(r[0], r[1][:22], r[idx['Email']][:32]) for r in wave[-3:]])

# WA candidates: mobile prefixes only, never contacted via WA
MOB_PREFIX = ('+447','447','+346','346','+3519','+393','393','+3538','+316','+9715','+1')
wa_c = []
for r in rows[1:]:
    st = (r[idx['Status']] or '')
    if re.search(r'whatsapp|wa sent|wa_|\bwa\b', st, re.I): continue
    ph = (r[idx['Phone']] or '').strip()
    if not ph or len(re.sub(r'\D', '', ph)) < 11: continue
    if any(ph.startswith(p) for p in MOB_PREFIX):
        wa_c.append(r)
print("WA mobile candidates:", len(wa_c))
print("WA first 10:", [(r[0], r[1][:20], r[idx['Phone']]) for r in wa_c[:10]])

# IG candidates
ig_c = [r for r in rows[1:] if (r[idx['IG Username']] or '').strip() and 'IG' not in (r[idx['Status']] or '')]
print("IG candidates (no 'IG' in status):", len(ig_c))

# duplicates check on normalized emails across whole file
seen, dupes = {}, 0
for r in rows[1:]:
    e = norm_email(r[idx['Email']]) if r[idx['Email']].strip() else ''
    if not e: continue
    if e in seen:
        dupes += 1
    else:
        seen[e] = r[0]
print("dupe emails in file:", dupes)
