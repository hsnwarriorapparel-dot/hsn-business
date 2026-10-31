#!/usr/bin/env python3
"""Rank the ammo left AFTER the Day-14 wave, using the proven wave-builder
scoring, so the top-up replacement is the strongest lead available."""
import csv, re, os
from urllib.parse import urlparse
from collections import Counter

CSV = '/home/ubuntu/leads.csv'
VERIFY = '/home/ubuntu/day14_site_verify.csv'
WAVE = set(l.strip() for l in open('/home/ubuntu/day14_wave.txt') if l.strip())

WEBMAIL = ('gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com', 'yahoo.fr',
           'yahoo.it', 'yahoo.es', 'yahoo.de', 'live.com', 'msn.com', 'aol.com',
           'mail.com', 'gmx.de', 'gmx.net', 'web.de', 't-online.de', 'orange.fr',
           'free.fr', 'laposte.net', 'libero.it', 'virgilio.it', 'tiscali.it',
           'protonmail.com', 'proton.me', 'icloud.com', 'me.com', 'zoho.com',
           'outlook.fr', 'outlook.it', 'outlook.de', 'wanadoo.fr', 'telenet.be',
           'skynet.be', 'home.nl', 'kpnmail.nl', 'ziggo.nl', 'planet.nl',
           'wp.pl', 'o2.pl', 'onet.pl', 'interia.pl', 'gazeta.pl', 'wp.com',
           'terra.com.br', 'uol.com.br', 'bol.com.br', 'sapo.pt', 'netcabo.pt',
           'seznam.cz', 'centrum.cz', 'at.sk', 'bluewin.ch', 'gmx.ch',
           'comcast.net', 'verizon.net', 'att.net', 'cox.net', 'charter.net',
           'sbcglobal.net', 'bellsouth.net', 'earthlink.net', 'yandex.com',
           'mail.ru', 'qq.com', '163.com', 'naver.com')

rows = list(csv.reader(open(CSV, newline='', encoding='utf-8-sig')))
hdr = rows[0]
idx = {h: i for i, h in enumerate(hdr)}
iE, iS, iW, iN, iC = idx['Email'], idx['Status'], idx['Website'], idx['Name'], idx['Country']

onsite = {}
if os.path.exists(VERIFY):
    for v in csv.DictReader(open(VERIFY, newline='', encoding='utf-8')):
        onsite[v['Lead ID']] = v['Result'] == 'ON-SITE'


def site_domain(w):
    w = (w or '').strip()
    if not w:
        return ''
    if not re.match(r'^https?://', w):
        w = 'http://' + w
    try:
        d = urlparse(w).netloc.lower()
    except Exception:
        return ''
    return d[4:] if d.startswith('www.') else d


def base(d):
    p = d.split('.')
    return '.'.join(p[-2:]) if len(p) >= 2 else d


ACTIVE = ('follow-up', 'hot lead', 'negotiat', 'sample quote', 'awaiting', 'replied')
scored = []
for r in rows[1:]:
    if len(r) <= iS:
        continue
    st = (r[iS] or '')
    sl = st.lower()
    e = (r[iE] or '').strip().lower()
    if not e or r[0] in WAVE:
        continue
    if 'email sent' in sl or 'failed' in sl or 'excluded' in sl or 're-hunt' in sl:
        continue
    if any(a in sl for a in ACTIVE):
        continue
    if not re.match(r'^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$', e):
        continue
    dom = e.split('@')[1]
    w = (r[iW] if len(r) > iW else '') or ''
    if not w.strip():
        continue
    sd = site_domain(w)
    sbase = base(sd) if sd else ''
    if sd and (base(dom) == sbase or dom in sd or sd in dom):
        kind, score = 'site-domain-match', 60
    elif onsite.get(r[0]):
        kind, score = 'verified-on-own-site', 50
    elif dom not in WEBMAIL:
        kind, score = 'business-domain-no-site', 12
    else:
        continue
    if dom not in WEBMAIL:
        score += 12
    local = e.split('@')[0]
    if local not in ('info', 'contact', 'contatos', 'contacto', 'hello', 'mail',
                     'email', 'office', 'admin', 'ventas', 'support', 'posta'):
        score += 8
    if '2026-10-28' in st:
        score += 8
    scored.append((score, r[0], (r[iN] or '')[:34], e, (r[iC] or '')[:14], kind, dom))

scored.sort(key=lambda x: (-x[0], int(re.sub(r'\D', '', x[1]) or 0)))
print('remaining ranked candidates:', len(scored))
print('kinds:', dict(Counter(s[5] for s in scored)))
print()
for s in scored[:12]:
    print('  ', s[0], s[1], '|', s[2], '|', s[3], '|', s[4], '|', s[5], '|', s[6])
