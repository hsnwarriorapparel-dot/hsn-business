#!/usr/bin/env python3
"""Day-15 ammo census: leads with an email, no 'email sent', no FAILED, no EXCLUDED."""
import csv, re, sys
from collections import Counter

CSV = '/home/ubuntu/leads.csv'
rows = list(csv.reader(open(CSV, encoding='utf-8', errors='replace')))
hdr = rows[0]
H = {h: i for i, h in enumerate(hdr)}

def g(r, k):
    i = H.get(k)
    return r[i] if i is not None and i < len(r) else ''

def norm(e):
    return re.sub(r'^(%20|u00a0|u003e|\s)+', '', (e or '').strip().lower()).lstrip('-.')

ammo = []
for r in rows[1:]:
    if len(r) <= H['Email']:
        continue
    e = norm(g(r, 'Email'))
    sl = (g(r, 'Status') or '').lower()
    if not e or '@' not in e:
        continue
    if 'email sent' in sl or 'failed' in sl or 'excluded' in sl or 're-hunt' in sl:
        continue
    if any(m in sl for m in ('follow-up', 'hot lead', 'negotiat', 'sample quote', 'awaiting', 'replied')):
        continue
    ammo.append((r[0], g(r, 'Name'), e, g(r, 'Country'), g(r, 'City'), g(r, 'Website'), sl[:60]))

print('TOTAL ROWS:', len(rows) - 1)
print('AMMO (email-ready):', len(ammo))
print('countries:', dict(Counter(a[3] or '?' for a in ammo)))
print('webmail count:', sum(1 for a in ammo if a[2].split('@')[1] in (
    'gmail.com','hotmail.com','outlook.com','yahoo.com','live.com','msn.com','aol.com',
    'gmx.de','gmx.net','web.de','orange.fr','free.fr','laposte.net','libero.it','virgilio.it',
    'tiscali.it','protonmail.com','proton.me','icloud.com','wp.pl','onet.pl','interia.pl',
    'web.de','mail.com','bluewin.ch','gmx.ch','comcast.net','verizon.net','att.net')))
print('fresh (2026-10-28/29):', sum(1 for a in ammo if '2026-10-28' in a[6] or '2026-10-29' in a[6]))
print('--- first 15 ---')
for a in ammo[:15]:
    print(' ', a[0], '|', a[1][:24], '|', a[2][:34], '|', a[3], '|', a[6][:40])
