#!/usr/bin/env python3
"""IG pass progress: how many wave leads / today's leads are done."""
import csv, re
from collections import Counter

rows = list(csv.DictReader(open('/home/ubuntu/leads.csv', newline='', encoding='utf-8')))
wave = set(l.strip() for l in open('/home/ubuntu/day14_wave.txt') if l.strip())
log = open('/home/ubuntu/day14_ig_log.txt').read()

done_ids = set(re.findall(r'(?:IG OK|MISMATCH|NOTFOUND) (L\d+)', log))
ok_ids = set(re.findall(r'IG OK \S+ @', log))
ok_leads = set(re.findall(r'IG OK .*?@(.*?) follow=', log))

# map handle->lead from log lines: "IG OK <name> @<handle> follow=..."
ok_lead_ids = set()
for m in re.finditer(r'IG OK .*?@(\S+)', log):
    pass
for line in log.splitlines():
    m = re.search(r'IG (OK|MISMATCH|NOTFOUND) (L\d+)', line)
    if m and m.group(1) == 'IG OK':
        ok_lead_ids.add(m.group(2))

wave_rows = [r for r in rows if r['Lead ID'] in wave]
wave_with_ig = [r for r in wave_rows if (r.get('IG Username') or '').strip()]
print('wave leads:', len(wave_rows), '| with IG handle:', len(wave_with_ig))
print('wave leads IG-done so far:', len([r for r in wave_with_ig if r['Lead ID'] in ok_lead_ids]))

today_hunted = [r for r in rows if '2026-10-28' in (r.get('Status') or '')]
today_with_ig = [r for r in today_hunted if (r.get('IG Username') or '').strip()]
print()
print('leads hunted today:', len(today_hunted), '| with IG handle:', len(today_with_ig))
print('today IG-done:', len([r for r in today_with_ig if r['Lead ID'] in ok_lead_ids]))

print()
print('log totals:', dict(Counter(re.findall(r'IG (?:OK|MISMATCH|NOTFOUND|ERR)', log))))
print('log lines processed:', len(done_ids))
