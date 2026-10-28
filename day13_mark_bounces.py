#!/usr/bin/env python3
"""Mark the 3 Day-13 bounces as EMAIL FAILED so they are never re-sent and
stop inflating the sent count. Bounce recipients were read from the Gmail
mailer-daemon threads (verified, not guessed)."""
import csv, os, tempfile

CSV = '/home/ubuntu/leads.csv'
DAY = 'Daily 2026-10-27'

# (email as it appears in the bounce notice, reason)
BOUNCES = [
    ('orienatlphoenixarts@gmail.com', 'recipient-not-registered (Blue Siytangco Taiji Kungfu)'),
    ('info@alphamaxbjj.ch', 'domain not found (Vera bjj kids)'),
    ('info@windycityboxing.com', 'address not found (Windy City Boxing)'),
]

rows = list(csv.reader(open(CSV, newline='', encoding='utf-8')))
idx = {h: i for i, h in enumerate(rows[0])}
iE, iS, iN = idx['Email'], idx['Status'], idx['Name']

hit = []
for r in rows[1:]:
    if not r:
        continue
    em = (r[iE] or '').strip().lower()
    for bad, reason in BOUNCES:
        if em == bad:
            # a bounce overrides the 'email sent' marker
            st = (r[iS] or '')
            st = st.replace(f'COMPLETE: email sent ({DAY})', '')
            st = st.replace(f'EMAIL FAILED ({DAY})', '')
            r[iS] = (st.rstrip(' |') + f' | EMAIL FAILED ({DAY}): {reason}')[:250]
            hit.append((r[0], (r[iN] or '')[:30], em))

fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
    csv.writer(f).writerows(rows)
os.replace(tmp, CSV)

chk = list(csv.reader(open(CSV, newline='', encoding='utf-8')))
c = {h: i for i, h in enumerate(chk[0])}
sent_today = sum(1 for r in chk[1:] if 'email sent (' + DAY + ')' in (r[c['Status']] or ''))
fail_today = sum(1 for r in chk[1:] if 'EMAIL FAILED (' + DAY + ')' in (r[c['Status']] or ''))
print('rows on disk:', len(chk) - 1)
print('bounce rows marked:', len(hit))
for h in hit:
    print('  ', h)
print('emails sent', DAY, ':', sent_today, '| failed', DAY, ':', fail_today)
