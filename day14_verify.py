#!/usr/bin/env python3
"""Day-12 (2026-10-27) final verification: exact counts read from disk.

Uses the canonical counters (hsn_counters.py) so every reported number uses
one definition. Read-only.
"""
import csv, re, sys
from collections import Counter
sys.path.insert(0, '/home/ubuntu')
import hsn_counters as C

CSV = '/home/ubuntu/leads.csv'
rows = list(csv.reader(open(CSV, encoding='utf-8', errors='replace')))
hdr = rows[0]
H = {h: i for i, h in enumerate(hdr)}


def g(r, k):
    i = H.get(k)
    return r[i] if i is not None and i < len(r) else ''


DAY = '2026-10-28'
today = [r for r in rows[1:] if DAY in g(r, 'Status')]
today_email = [r for r in today if C.email_ok(r)]
today_ig = [r for r in today if C.ig_ok(r)]
today_wa = [r for r in today if C.wa_ok(r)]
today_fail = [r for r in today if 'failed' in g(r, 'Status').lower()]

ammo = 0
for r in rows[1:]:
    e = g(r, 'Email').strip()
    s = g(r, 'Status').lower()
    if not e:
        continue
    if 'email sent' in s or 'failed' in s or 'excluded' in s or 're-hunt' in s:
        continue
    if any(m in s for m in ['follow-up', 'hot lead', 'negotiat', 'sample quote', 'awaiting', 'replied']):
        continue
    ammo += 1

ids = [int(m.group(1)) for r in rows[1:] for m in [re.match(r'L(\d+)$', (r[0] or '').strip())] if m]
wa_pending = [r for r in rows[1:] if g(r, 'Phone').strip() and not C.wa_ok(r)
              and 'not on whatsapp' not in g(r, 'Status').lower()
              and "isn't on whatsapp" not in g(r, 'Status').lower()]

print('=' * 58)
print('LEADS TOTAL:', len(rows) - 1, '| with email:', sum(1 for r in rows[1:] if g(r, 'Email').strip()),
      '| with phone:', sum(1 for r in rows[1:] if g(r, 'Phone').strip()))
print('CAMPAIGN TOTALS -> emails sent:', C.count(C.email_ok),
      '| IG follow+DM:', C.count(C.ig_ok),
      '| WA sent:', C.count(C.wa_ok), '| HOT leads:', C.count(C.hot))
print('failed:', sum(1 for r in rows[1:] if 'failed' in g(r, 'Status').lower()),
      '| excluded:', sum(1 for r in rows[1:] if 'excluded' in g(r, 'Status').lower()),
      '| remaining ammo:', ammo)
print('max Lead ID: L%d' % max(ids))
print('=' * 58)
print(f'TODAY {DAY} rows touched:', len(today))
print('  emails sent today:', len(today_email))
print('  IG follow+DM today:', len(today_ig))
print('  WA sent today:', len(today_wa))
print('  failures today:', len(today_fail))
for r in today_fail[:12]:
    print('    FAIL:', r[0], (g(r, 'Name') or '')[:26], '|', g(r, 'Status')[:90])
print('  countries of today emails:', dict(Counter(g(r, 'Country') or '?' for r in today_email)))
print('=' * 58)
print('WA pending numbers (not messaged):', len(wa_pending))
