#!/usr/bin/env python3
"""Fix false WA-FAILED markers from the Day 9 session drop (9 leads hit the QR screen,
never actually attempted). Restore them as fresh candidates + verify L797 marker."""
import csv, os, tempfile

CSV = '/home/ubuntu/leads.csv'
FALSE_FAILS = ['L800', 'L805', 'L810', 'L811', 'L817', 'L818', 'L822', 'L828', 'L829']
EXPECT_SENT = 'L797'

rows = list(csv.reader(open(CSV, newline='', encoding='utf-8')))
idx = {h: i for i, h in enumerate(rows[0])}
iS = idx['Status']

cleaned = []
l797_status = None
for r in rows[1:]:
    if r[0] in FALSE_FAILS:
        before = r[iS]
        # strip the false failure marker, keep the honest history note
        parts = [p.strip() for p in before.split('|')]
        keep = [p for p in parts if 'WA FAILED' not in p.upper()]
        r[iS] = ' | '.join(keep) + ' | WA retry-queued (Day 9: WA session died before attempt)'
        cleaned.append((r[0], r[iS][-70:]))
    if r[0] == EXPECT_SENT:
        l797_status = r[iS]

fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
    csv.writer(f).writerows(rows)
os.replace(tmp, CSV)

rows2 = list(csv.reader(open(CSV, newline='', encoding='utf-8')))
assert len(rows2) == len(rows), "row count changed!"
print(f"rows verified: {len(rows2)}")
print(f"L797 status: {l797_status}")
for lid, st in cleaned:
    print(f"  {lid}: ...{st}")
# confirm no 'WA FAILED (Day 9)' remains on those rows
leftover = [r[0] for r in rows2[1:] if r[0] in FALSE_FAILS and 'WA FAILED (Day 9)' in r[idx['Status']]]
print("leftover false markers:", leftover if leftover else "NONE (clean)")
