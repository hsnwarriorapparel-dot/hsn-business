#!/usr/bin/env python3
"""Check Day 8 WA state + fresh candidates."""
import csv, re

rows = list(csv.reader(open('/home/ubuntu/leads.csv')))
idx = {h: i for i, h in enumerate(rows[0])}

wa8 = [r for r in rows[1:] if 'WA sent (Day 8)' in r[idx['Status']]]
print(f'Day 8 WA sent: {len(wa8)}')

# log check
try:
    log = open('/home/ubuntu/day8_log.txt').read()
    import re as _re
    wa_ok = len(_re.findall(r'WA .*: OK', log))
    print(f'Day 8 log WA OK lines: {wa_ok}')
    for line in log.split('\n'):
        if 'WA' in line or 'STAGE' in line:
            print('  ', line[:80])
except Exception as e:
    print('log read error:', e)

fresh = [r for r in rows[1:] if (r[idx['Phone']] or '').strip() and len(r[idx['Phone']].strip()) >= 11
         and 'WA' not in r[idx['Status']] and 'wa=' not in r[idx['Status']].lower()]
print(f'\nFresh WA candidates: {len(fresh)}')
for r in fresh[:14]:
    print(f'  {r[0]} {r[1][:24]} | {r[idx["Phone"]][:18]} | {r[idx["Country"]][:12]} | {r[idx["Status"]][:36]}')
