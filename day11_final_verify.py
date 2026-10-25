#!/usr/bin/env python3
"""Day-11 final verification: read the CSV from disk and report exact counts.
Read-only. Used for the cron report — every number comes from disk."""
import csv, re, sys
from collections import Counter

CSV = '/home/ubuntu/leads.csv'
rows = list(csv.reader(open(CSV, encoding='utf-8', errors='replace')))
hdr = rows[0]
H = {h: i for i, h in enumerate(hdr)}


def g(r, k):
    i = H.get(k)
    return r[i] if i is not None and i < len(r) else ''


def st(r):
    return g(r, 'Status').lower()


total = len(rows)
with_email = sum(1 for r in rows if g(r, 'Email').strip())
sent = sum(1 for r in rows if 'email sent' in st(r))
failed = sum(1 for r in rows if 'failed' in st(r))
excluded = sum(1 for r in rows if 'excluded' in st(r))
ig = sum(1 for r in rows if 'ig follow' in st(r) or 'dm=sent' in st(r))
wa = sum(1 for r in rows if 'whatsapp sent' in st(r) or 'wa sent' in st(r))
hot = sum(1 for r in rows if 'HOT' in g(r, 'Status').upper())
phone = sum(1 for r in rows if g(r, 'Phone').strip())

# today
today = [r for r in rows if '2026-10-25' in g(r, 'Status')]
today_email = [r for r in today if 'email sent' in st(r)]
today_ig = [r for r in today if 'ig follow' in st(r) or 'dm=sent' in st(r)]
today_failed = [r for r in today if 'failed' in st(r)]

# remaining ammo
ammo = 0
for r in rows:
    e = g(r, 'Email').strip()
    s = st(r)
    if not e:
        continue
    if 'email sent' in s or 'failed' in s or 'excluded' in s or 're-hunt' in s:
        continue
    if any(m in s for m in ['follow-up', 'hot lead', 'negotiat', 'sample quote', 'awaiting', 'replied']):
        continue
    ammo += 1

ids = [int(m.group(1)) for r in rows for m in [re.match(r'L(\d+)$', (r[0] or '').strip())] if m]
print("=" * 56)
print("LEADS TOTAL:", total, "| with email:", with_email, "| with phone:", phone)
print("CAMPAIGN TOTALS -> emails sent:", sent, "| IG follow+DM:", ig,
      "| WA sent:", wa, "| HOT leads:", hot)
print("failed:", failed, "| excluded:", excluded, "| remaining ammo:", ammo)
print("max Lead ID: L%d" % max(ids))
print("=" * 56)
print("TODAY 2026-10-25 rows touched:", len(today))
print("  emails sent today:", len(today_email))
print("  IG follow+DM today:", len(today_ig))
print("  failures today:", len(today_failed))
for r in today_failed[:10]:
    print("    FAIL:", r[0], (g(r, 'Name') or '')[:26], '|', g(r, 'Status')[:90])
print("  countries of today's emails:", dict(Counter(g(r, 'Country') or '?' for r in today_email)))
print("=" * 56)
# WA pending (numbers not yet messaged)
wa_pending = [r for r in rows if g(r, 'Phone').strip()
              and 'whatsapp sent' not in st(r) and 'wa sent' not in st(r)
              and 'not on whatsapp' not in st(r)]
print("WA pending numbers (not messaged):", len(wa_pending))
