#!/usr/bin/env python3
"""Re-mark wave leads whose email-sent marker was clobbered by a concurrent
full-file CSV writer. Uses the Gmail-verified audit (day13_marker_audit.json):
only leads with a confirmed Gmail Sent conversation get the marker back.
Row-targeted read -> write -> atomic replace, then read-back."""
import csv, os, tempfile, json

CSV = '/home/ubuntu/leads.csv'
AUDIT = '/home/ubuntu/day13_marker_audit.json'
DAY = 'Daily 2026-10-27'
MARK = f"COMPLETE: email sent ({DAY})"

audit = json.load(open(AUDIT))
confirmed = {lid: n for lid, n in audit.items() if n == 1}
print('audit entries:', len(audit), '| confirmed sent (=1):', len(confirmed))

rows = list(csv.reader(open(CSV, newline='', encoding='utf-8-sig')))
idx = {h: i for i, h in enumerate(rows[0])}
iS = idx['Status']
fixed = []
for r in rows[1:]:
    if not r:
        continue
    lid = r[0]
    if lid in confirmed and 'email sent' not in (r[iS] or '').lower():
        r[iS] = (r[iS].rstrip(' |') + ' | ' + MARK)[:250]
        fixed.append(lid)

if fixed:
    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(rows)
    os.replace(tmp, CSV)

chk = list(csv.reader(open(CSV, newline='', encoding='utf-8-sig')))
c = {h: i for i, h in enumerate(chk[0])}
sent_today = sum(1 for r in chk[1:] if 'email sent (' + DAY + ')' in (r[c['Status']] or ''))
wave = [l.strip() for l in open('/home/ubuntu/day13_wave.txt') if l.strip()]
d = {r[0]: r for r in chk[1:]}
missing = [l for l in wave if 'email sent' not in (d[l][c['Status']] or '').lower()] if all(l in d for l in wave) else []
print('rows on disk:', len(chk) - 1)
print('re-marked:', len(fixed), fixed)
print('emails sent with', DAY, ':', sent_today)
print('wave leads still missing the marker:', len(missing), missing)
