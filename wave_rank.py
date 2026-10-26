#!/usr/bin/env python3
"""Day-11 wave prioritization analysis (read-only).
Scores every ammo lead on:
  - website<->email domain match (strongest signal the address belongs to the gym)
  - business domain vs webmail
  - generic local part vs specific
  - name quality (placeholder/initialism)
  - hunt freshness (gmaps 2026-10-25 newest > 2026-10-24 > 2026-10-23 > older)
Prints the top-120 ranked wave so the send order is quality-first.
"""
import csv, re
from urllib.parse import urlparse
from collections import Counter

CSV = '/home/ubuntu/leads.csv'
WEBMAIL = ('gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com', 'yahoo.fr',
           'yahoo.it', 'yahoo.es', 'yahoo.de', 'live.com', 'msn.com', 'aol.com',
           'mail.com', 'gmx.de', 'gmx.net', 'web.de', 't-online.de', 'orange.fr',
           'free.fr', 'laposte.net', 'libero.it', 'virgilio.it', 'tiscali.it',
           'protonmail.com', 'proton.me', 'icloud.com', 'me.com', 'zoho.com')
GENERIC_LOCAL = {'info', 'contact', 'contatos', 'contacto', 'hello', 'hi', 'mail',
                 'email', 'webmaster', 'admin', 'office', 'ventas', 'recepcion',
                 'recepción', 'support', 'kontakt', 'posta', 'reception'}
BAD_NAME = {'unknown gym', 'n/a', 'na', 'info', 'contactos', 'contact', 'contact us',
            'kontakt', 'impressum', 'sin nombre', 'admin', 'office', 'mail', 'email',
            'webmaster', 'hello', 'ventas', 'recepcion', 'recepción', 'gym', 'academy',
            'academia', 'club', 'unknown', 'none', '-', '--', 'asmbf', 'asmbf club'}


def norm_email(e):
    return re.sub(r'^(%20|u00a0|\s)+', '', (e or '').strip().lower())


def valid_email(e):
    e = norm_email(e)
    return bool(re.match(r'^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$', e)) and 'http' not in e


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


def base_dom(d):
    p = d.split('.')
    return '.'.join(p[-2:]) if len(p) >= 2 else d


rows = list(csv.reader(open(CSV, encoding='utf-8', errors='replace')))
idx = {h: i for i, h in enumerate(rows[0])}
iE, iS, iW, iN, iC, iIG = (idx['Email'], idx['Status'], idx['Website'],
                           idx['Name'], idx['Country'], idx['IG Username'])
ACTIVE = ['follow-up', 'hot lead', 'negotiat', 'sample quote', 'awaiting', 'replied']

scored = []
for r in rows[1:]:
    if len(r) <= iS:
        continue
    st = (r[iS] or '')
    sl = st.lower()
    e = norm_email(r[iE] or '')
    if not e or not valid_email(e):
        continue
    if 'email sent' in sl or 'failed' in sl or 'excluded' in sl or 're-hunt' in sl:
        continue
    if any(m in sl for m in ACTIVE):
        continue
    dom = e.split('@')[1]
    local = e.split('@')[0]
    sd = site_domain(r[iW] if len(r) > iW else '')
    score = 0
    reasons = []
    if sd:
        if base_dom(dom) == base_dom(sd):
            score += 50; reasons.append('domain-match')
        elif dom in sd or sd in dom:
            score += 35; reasons.append('domain-partial')
    if dom not in WEBMAIL:
        score += 20; reasons.append('business-domain')
    else:
        reasons.append('webmail')
    if local not in GENERIC_LOCAL:
        score += 10; reasons.append('specific-local')
    name = (r[iN] or '').strip()
    nl = re.sub(r'[^a-z0-9]', '', name.lower())
    if name.lower() in BAD_NAME or len(nl) < 5:
        score -= 25; reasons.append('WEAK-NAME')
    if re.fullmatch(r'[a-z]{2,6}', name.lower()) and len(name) <= 6:
        score -= 10; reasons.append('initialism-name')
    fresh = 0
    if '2026-10-25' in st: fresh = 4
    elif '2026-10-24' in st: fresh = 3
    elif '2026-10-23' in st: fresh = 2
    elif 'day 9' in sl or 'day 10' in sl: fresh = 1
    score += fresh
    ig = bool((r[iIG] or '').strip())
    scored.append((score, r[0], name, e, r[iC] or '?', fresh, ','.join(reasons), ig))

scored.sort(key=lambda x: (-x[0], int(re.sub(r'\D', '', x[1]) or 0)))
print("ammo scored:", len(scored))
print("score distribution:", dict(Counter(s[0] for s in scored).most_common(14)))
print("countries of top-100:", dict(Counter(s[4] for s in scored[:100])))
print("webmail in top-100:", sum(1 for s in scored[:100] if 'webmail' in s[6]))
print("weak names in top-100:", sum(1 for s in scored[:100] if 'WEAK-NAME' in s[6]))
print("domain-matched in top-100:", sum(1 for s in scored[:100] if 'domain-match' in s[6]))
print("IG handle present in top-100:", sum(1 for s in scored[:100] if s[7]))
print()
for s in scored[:120]:
    print(f"{s[0]:4} | {s[1]:6} | {s[2][:30]:30} | {s[3][:38]:38} | {s[4][:13]:13} | {s[6]}")
