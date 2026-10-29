#!/usr/bin/env python3
"""Day-14 ammo census v2 - exclude client conversations (replied/hot) too."""
import csv
from collections import Counter

CSV = '/home/ubuntu/leads.csv'
rows = list(csv.DictReader(open(CSV, newline='', encoding='utf-8')))

def norm(e):
    return (e or '').strip().lower()

def status(r):
    return (r.get('Status') or '')

ammo, excluded_client = [], []
for r in rows:
    e = norm(r.get('Email'))
    if not e:
        continue
    sl = status(r).lower()
    if 'email sent' in sl or 'failed' in sl or 'excluded' in sl:
        continue
    if 'replied' in sl or 'hot lead' in sl or 'follow-up sent' in sl or 'contacted' in sl:
        excluded_client.append(r)
        continue
    ammo.append(r)

print('AMMO (clean):', len(ammo))
print('excluded client-conversation rows:', len(excluded_client))
for r in excluded_client[:15]:
    print('  ', r.get('Lead ID'), r.get('Name'), '|', status(r)[:70])
print()
print('countries:', Counter((r.get('Country') or '?').strip().lower() for r in ammo).most_common())
print('status kinds:', Counter(status(r).split(';')[0][:34] for r in ammo).most_common(10))
print('has IG:', sum(1 for r in ammo if (r.get('IG Username') or '').strip()))
print('has phone:', sum(1 for r in ammo if (r.get('Phone') or '').strip()))
print('has website:', sum(1 for r in ammo if (r.get('Website') or '').strip()))
# distribution by hunt date in status
print('by hunt tag:', Counter(t for t in [next((w for w in status(r).split() if w.startswith('HUNTED')), 'other') for r in ammo]).most_common(12))
