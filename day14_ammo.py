#!/usr/bin/env python3
"""Day-14 ammo census: leads with an email, no 'email sent', no FAILED, no EXCLUDED."""
import csv, re, sys

CSV = '/home/ubuntu/leads.csv'
rows = list(csv.DictReader(open(CSV, newline='', encoding='utf-8-sig')))
print('total rows:', len(rows))

def norm(e):
    return (e or '').strip().lower()

ammo = []
for r in rows:
    st = (r.get('Status') or '')
    e = norm(r.get('Email'))
    if not e:
        continue
    sl = st.lower()
    if 'email sent' in sl:
        continue
    if 'failed' in sl:
        continue
    if 'excluded' in sl:
        continue
    ammo.append(r)

print('AMMO COUNT:', len(ammo))
from collections import Counter
print('countries:', Counter((r.get('Country') or '?').strip().lower() for r in ammo).most_common(15))
print('has website:', sum(1 for r in ammo if (r.get('Website') or '').strip()))
print('has IG:', sum(1 for r in ammo if (r.get('IG Username') or '').strip()))
print('has phone:', sum(1 for r in ammo if (r.get('Phone') or '').strip()))
doms = Counter()
for r in ammo:
    e = norm(r.get('Email'))
    if '@' in e:
        d = e.split('@')[-1]
        d = d.strip()
        doms[d] += 1
print('top domains:', doms.most_common(12))
print('--- first 15 ---')
for r in ammo[:15]:
    print(r.get('Lead ID'), '|', (r.get('Name') or '')[:28], '|', r.get('Country'), '|', norm(r.get('Email')), '|', (r.get('Status') or '')[:40])
