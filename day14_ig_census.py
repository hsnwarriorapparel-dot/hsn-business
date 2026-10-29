#!/usr/bin/env python3
"""How many of TODAY's leads still need an IG handle (read-only)."""
import csv

rows = list(csv.DictReader(open('/home/ubuntu/leads.csv', newline='', encoding='utf-8')))
wave = set(l.strip() for l in open('/home/ubuntu/day14_wave.txt') if l.strip())

def has_ig(r):
    return (r.get('IG Username') or '').strip().lstrip('@').strip() != ''

wave_rows = [r for r in rows if r['Lead ID'] in wave]
print('wave leads:', len(wave_rows))
print('  with IG handle:', sum(1 for r in wave_rows if has_ig(r)))
print('  missing IG handle:', sum(1 for r in wave_rows if not has_ig(r)))

# leads HUNTED today (2026-10-28) = found today -> same-day IG rule
today_hunted = [r for r in rows if '2026-10-28' in (r.get('Status') or '')]
print()
print('leads hunted today (2026-10-28):', len(today_hunted))
print('  with IG handle:', sum(1 for r in today_hunted if has_ig(r)))
print('  missing IG handle:', sum(1 for r in today_hunted if not has_ig(r)))

# overall backlog missing a handle
all_missing = [r for r in rows if not has_ig(r) and (r.get('Website') or '').strip()]
print()
print('ALL leads missing an IG handle (have website):', len(all_missing))
noday = [r for r in all_missing if '2026-10-28' not in (r.get('Status') or '')]
print('  of those, NOT hunted today (backlog):', len(noday))
