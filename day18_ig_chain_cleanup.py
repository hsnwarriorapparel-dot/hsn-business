#!/usr/bin/env python3
"""Day-18 IG chain-duplicate cleanup (2026-11-01).

A multi-branch chain (TITLE Boxing Club, Rumble Boxing) lists the SAME
chain-level Instagram account on every branch page, so the IG pass sent a
second DM to the same handle for each sibling branch.

This script finds every handle that received MORE THAN ONE DM on 2026-11-01
and marks the LATER rows as 'dm=chain-dup' so the counter counts ONE DM per
Instagram account, not one per branch. It does NOT send anything - it only
corrects the Status markers. It must run AFTER the IG pass finished.
"""
import csv, os, re, sys, tempfile

CSV = '/home/ubuntu/leads.csv'
DAY = 'Daily 2026-11-01'


def update_status(lead_id, new_status):
    rows = list(csv.reader(open(CSV, newline='', encoding='utf-8-sig')))
    idx = {h: i for i, h in enumerate(rows[0])}
    hit = False
    for r in rows[1:]:
        if r and r[0] == lead_id:
            r[idx['Status']] = (r[idx['Status']].rstrip(' |') + ' | ' + new_status)[:250]
            hit = True
    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(rows)
    os.replace(tmp, CSV)
    return hit


rows = list(csv.DictReader(open(CSV, newline='', encoding='utf-8-sig')))
by_handle = {}
for r in rows:
    st = r.get('Status') or ''
    if DAY not in st:
        continue
    if 'dm=sent' not in st:
        continue
    h = (r.get('IG Username') or '').strip().lstrip('@').lower()
    if not h:
        continue
    by_handle.setdefault(h, []).append(r)

dups = []
for h, group in by_handle.items():
    if len(group) > 1:
        group.sort(key=lambda r: int(re.sub(r'\D', '', r['Lead ID']) or 0))
        for r in group[1:]:
            dups.append((h, r['Lead ID'], r.get('Name') or ''))

print('handles with >1 DM today:', sum(1 for g in by_handle.values() if len(g) > 1))
print('duplicate rows to mark:', len(dups))
for h, lid, name in dups:
    ok = update_status(lid, 'IG dm=chain-dup (same chain IG account as a sibling branch - one DM per account)')
    print(f'  MARK {lid} @{h} {name[:30]} written={ok}')

chk = list(csv.DictReader(open(CSV, newline='', encoding='utf-8-sig')))
still = 0
for r in chk:
    st = r.get('Status') or ''
    if DAY in st and 'dm=sent' in st:
        h = (r.get('IG Username') or '').strip().lstrip('@').lower()
        if h and sum(1 for x in by_handle.get(h, []) if x['Lead ID'] == r['Lead ID']) > 1:
            still += 1
print('remaining rows still carrying dm=sent on a duplicated handle:', still)
