#!/usr/bin/env python3
"""Read-only classification of all Day-5 USA leads: sendable emails vs suspect vs none.
No writes, no sends. Output feeds the morning report."""
import csv
from collections import Counter

CSV = '/home/ubuntu/leads.csv'
BAD_DOMAIN = ('usaboxing.org', 'teamusa', 'reddit', 'yelp', 'classpass', 'tripadvisor',
              'thumbtack', 'meetup', 'yellowpages', 'mysite.com', 'squarespace.com',
              'wixpress.com', 'example.com', 'latofonts.com', 'godaddy.com', 'sentry.io',
              'email.com', 'mail.com', 'test.com', 'domain.com', 'yourdomain.com')

with open(CSV) as f:
    rows = list(csv.DictReader(f))

d5 = [r for r in rows if 'Day 5 USA' in (r.get('Notes') or '')]
print("Day-5 USA leads:", len(d5))

def classify(email):
    e = (email or '').strip().lower()
    if not e:
        return 'NO-EMAIL'
    if '@' not in e:
        return 'MALFORMED'
    d = e.split('@')[-1]
    if d in BAD_DOMAIN:
        return f'SUSPECT-DOMAIN({d})'
    if '.' not in d:
        return 'MALFORMED'
    return 'OK'

buckets = Counter()
suspect_list = []
for r in d5:
    c = classify(r.get('Email'))
    buckets[c if c == 'OK' or c == 'NO-EMAIL' else ('MALFORMED' if c == 'MALFORMED' else 'SUSPECT')] += 1
    if c not in ('OK', 'NO-EMAIL'):
        suspect_list.append((r['Lead ID'], r['Name'][:24], r.get('Email'), c))

print("\nEMAIL CLASSIFICATION:")
for k in ('OK', 'SUSPECT', 'MALFORMED', 'NO-EMAIL'):
    print(f"  {k}: {buckets.get(k, 0)}")

print("\nSUSPECT/MALFORMED DETAIL:")
for lid, name, email, why in suspect_list:
    print(f"  {lid} | {name} | {email} | {why}")

ig_with = sum(1 for r in d5 if ((r.get('IG Username') or '') + (r.get('IG Profile Link') or '')).strip())
print(f"\nIG handles: {ig_with} | no IG: {len(d5) - ig_with}")
print(f"Phones remaining after cleanup: {sum(1 for r in d5 if (r.get('Phone') or '').strip())}")

dup = [e for e, c in Counter((r.get('Email') or '').strip().lower() for r in d5 if r.get('Email')).items() if c > 1]
print(f"Duplicate emails within Day 5: {len(dup)} {dup[:5]}")
