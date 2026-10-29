#!/usr/bin/env python3
"""Day-14: mark the Spear Jiu Jitsu bounce as EMAIL FAILED (so it is never
re-sent and never counted as delivered) and pick a TOP-UP lead so the day
still lands on 100 DELIVERED emails.

Fresh read -> modify -> atomic write -> read-back verification.
Row-targeted semantics: only the ONE row's Status changes.
"""
import csv, os, sys, tempfile, re
from urllib.parse import urlparse

CSV = '/home/ubuntu/leads.csv'
DAY = 'Daily 2026-10-28'
BOUNCE = ('spearpay@spearjiujitsu.com', 'domain not found (Spear Jiu Jitsu)')
WEBMAIL = ('gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com', 'yahoo.fr',
           'yahoo.it', 'yahoo.es', 'yahoo.de', 'live.com', 'msn.com', 'aol.com',
           'mail.com', 'gmx.de', 'gmx.net', 'web.de', 't-online.de', 'orange.fr',
           'free.fr', 'laposte.net', 'libero.it', 'virgilio.it', 'tiscali.it',
           'protonmail.com', 'icloud.com', 'me.com', 'zoho.com', 'outlook.fr',
           'outlook.it', 'outlook.de', 'bluewin.ch', 'gmx.ch', 'comcast.net',
           'verizon.net', 'att.net', 'cox.net', 'charter.net', 'sbcglobal.net',
           'bellsouth.net', 'earthlink.net', 'yandex.com', 'mail.ru', 'qq.com')
PLACEHOLDER = ('beispiel', 'example.com', 'domain.com', 'dominio.com', 'mysite.com',
               'test.com', 'sample.com', 'yourdomain', 'mydomain', 'exemplo',
               'placeholder', 'mustermann', 'dummy')

rows = list(csv.reader(open(CSV, newline='', encoding='utf-8')))
hdr = rows[0]
idx = {h: i for i, h in enumerate(hdr)}
iE, iS, iN, iC, iW = idx['Email'], idx['Status'], idx['Name'], idx['Country'], idx['Website']

# ---------- 1. mark the bounce ----------
marked = []
for r in rows[1:]:
    if not r:
        continue
    em = (r[iE] or '').strip().lower()
    if em == BOUNCE[0]:
        st = (r[iS] or '')
        st = st.replace(f'COMPLETE: email sent ({DAY})', '')
        r[iS] = (st.rstrip(' |') + f' | EMAIL FAILED ({DAY}): {BOUNCE[1]}')[:250]
        marked.append((r[0], (r[iN] or '')[:30], em))

# ---------- 2. pick the top-up lead ----------
onsite = {}
if os.path.exists('/home/ubuntu/day14_site_verify.csv'):
    for v in csv.DictReader(open('/home/ubuntu/day14_site_verify.csv', newline='')):
        onsite[v['Lead ID']] = v['Result'] == 'ON-SITE'

from collections import Counter
email_counts = Counter()
for r in rows[1:]:
    if len(r) > iE:
        e = (r[iE] or '').strip().lower()
        if e:
            email_counts[e] += 1

ACTIVE = ('follow-up', 'hot lead', 'negotiat', 'sample quote', 'awaiting', 'replied')
cands = []
for r in rows[1:]:
    if len(r) <= iS:
        continue
    st = (r[iS] or '')
    sl = st.lower()
    e = (r[iE] or '').strip().lower()
    # a duplicate = this address appears on an EARLIER row too. A single
    # occurrence is fine (it is just an un-sent lead, which is what we want).
    if not e:
        continue
    if email_counts[e] > 1 and email_counts[e] > 1:
        prior = [x for x in rows[1:] if len(x) > iE and (x[iE] or '').strip().lower() == e]
        if prior and prior[0][0] != r[0]:
            continue
    if 'email sent' in sl or 'failed' in sl or 'excluded' in sl or 're-hunt' in sl:
        continue
    if any(a in sl for a in ACTIVE):
        continue
    if not re.match(r'^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$', e):
        continue
    dom = e.split('@')[1]
    if any(p in dom for p in PLACEHOLDER):
        continue
    if dom.endswith('pec.it') or ',' in e or ' ' in e:
        continue
    w = (r[iW] if len(r) > iW else '') or ''
    if not w.strip():
        continue
    # business domain matching its own site is the strongest signal
    try:
        sd = urlparse(w if w.startswith('http') else 'http://' + w).netloc.lower()
        sd = sd[4:] if sd.startswith('www.') else sd
    except Exception:
        sd = ''
    sbase = '.'.join(sd.split('.')[-2:]) if sd else ''
    dbase = '.'.join(dom.split('.')[-2:])
    score = 0
    if sd and (dbase == sbase or dom in sd or sd in dom):
        score = 60
    elif onsite.get(r[0]):
        score = 50
    elif dom not in WEBMAIL:
        score = 20
    else:
        continue
    if '2026-10-28' in sl:
        score += 8
    cands.append((score, r[0], (r[iN] or '')[:34], e, (r[iC] or '')[:16], dom))

cands.sort(key=lambda x: (-x[0], int(re.sub(r'\D', '', x[1]) or 0)))
print('marked bounce rows:', marked)
print('top-up candidates:', len(cands))
for c in cands[:8]:
    print('   CAND', c)
pick = cands[0] if cands else None
if pick:
    with open('/home/ubuntu/day14_topup.txt', 'w') as f:
        f.write(pick[1] + '\n')
    print('TOP-UP PICKED:', pick[1], pick[2], pick[3])

# ---------- 3. atomic write + read-back ----------
# FRESH RE-READ immediately before the write: the IG pass may have marked rows
# while this script was running, and a stale in-memory copy would clobber
# those markers (Day-13 lesson: never write a stale full-file copy).
fresh = list(csv.reader(open(CSV, newline='', encoding='utf-8')))
fidx = {h: i for i, h in enumerate(fresh[0])}
for r in fresh[1:]:
    if not r:
        continue
    em = (r[fidx['Email']] or '').strip().lower()
    if em == BOUNCE[0]:
        st = (r[fidx['Status']] or '')
        if 'EMAIL FAILED' not in st:
            st = st.replace(f'COMPLETE: email sent ({DAY})', '')
            r[fidx['Status']] = (st.rstrip(' |') + f' | EMAIL FAILED ({DAY}): {BOUNCE[1]}')[:250]
fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
    csv.writer(f).writerows(fresh)
os.replace(tmp, CSV)

chk = list(csv.reader(open(CSV, newline='', encoding='utf-8')))
c = {h: i for i, h in enumerate(chk[0])}
sent = sum(1 for r in chk[1:] if f'email sent ({DAY})' in (r[c['Status']] or ''))
fail = sum(1 for r in chk[1:] if f'EMAIL FAILED ({DAY})' in (r[c['Status']] or ''))
print('rows on disk:', len(chk) - 1)
print(f'emails sent {DAY}: {sent} | failed {DAY}: {fail}')
for r in chk[1:]:
    if (r[c['Email']] or '').strip().lower() == BOUNCE[0]:
        print('  VERIFY bounce row:', r[0], '|', r[c['Status']][:110])
