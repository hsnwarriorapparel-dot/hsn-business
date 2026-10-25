#!/usr/bin/env python3
"""Day-11 pre-flight QA (2026-10-25): replicate day6_pipeline filters EXACTLY,
then flag name-quality / contamination issues before any email is sent.

Read-only. Prints the wave that day6_pipeline.py would fire.
"""
import csv, re, json
from collections import Counter

CSV = '/home/ubuntu/leads.csv'
rows = list(csv.reader(open(CSV, encoding='utf-8', errors='replace')))
hdr = rows[0]
idx = {h: i for i, h in enumerate(hdr)}
iE, iP, iIG, iS, iC, iN, iW = (idx['Email'], idx['Phone'], idx['IG Username'],
                               idx['Status'], idx['Country'], idx['Name'], idx['Website'])

# ---- exact copies of day6_pipeline.py filters ----
ACTIVE  = ['follow-up', 'hot lead', 'negotiat', 'sample quote', 'awaiting', 'replied']
FED     = ['federation', 'verband', 'association', 'bonds', 'federal', 'excluded']
PERSONAL = ['sayyam', 'shamas', 'afzal', 'chacho nadeem']

def valid_email(e):
    e = re.sub(r'^(%20|u00a0|\s)+', '', (e or '').strip().lower())
    return bool(re.match(r'^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$', e)) and 'http' not in e

def norm_email(e):
    return re.sub(r'^(%20|u00a0|\s)+', '', (e or '').strip().lower())

# ---- contamination filters for QA ----
GENERIC = ('gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com', 'yahoo.fr',
           'yahoo.it', 'yahoo.es', 'yahoo.de', 'live.com', 'msn.com', 'aol.com',
           'mail.com', 'gmx.de', 'gmx.net', 'web.de', 't-online.de', 'orange.fr',
           'wanadoo.fr', 'free.fr', 'laposte.net', 'libero.it', 'virgilio.it',
           'tiscali.it', 'terra.com.br', 'uol.com.br', 'bol.com.br', 'sapo.pt',
           'naver.com', 'qq.com', '163.com', '126.com', 'icloud.com', 'me.com',
           'mac.com', 'protonmail.com', 'proton.me', 'zoho.com', 'yandex.com')
FED_DOMAINS = ('ffjudo', 'ffkarate', 'fijlkam', 'judobund', 'wako', 'britishjudo',
               'ffboxe', 'kickboxen-deutschland', 'fkb.nl', 'usaboxing', 'trouver-un-club',
               'kombazen', 'ffsavate', 'ifbb', 'ibaf', 'uisa', 'teamusa', 'ijf.org',
               'uww', 'imaf', 'wushu', 'euro-athletics', 'theijf', 'fisu')
PLACEHOLDER_NAMES = ('unknown gym', 'n/a', 'na', 'info', 'contactos', 'contact',
                      'contact us', 'kontakt', 'impressum', 'contactenos', 'dónde boxeo',
                      'dove boxeo', 'sin nombre', 'admin', 'office', 'mail', 'email',
                      'webmaster', 'hello', 'ventas', 'recepcion', 'recepción', 'gym',
                      'academy', 'academia', 'club', 'unknown', 'none', '-', '--')

ammo_all, invalid, excluded_active = [], [], []
for r in rows[1:]:
    if len(r) <= iS:
        continue
    st = (r[iS] or '').lower()
    if not (r[iE] or '').strip():
        continue
    if 'email sent' in st or 'failed' in st or 're-hunt' in st or 'excluded' in st:
        continue
    if any(m in st for m in ACTIVE):
        excluded_active.append(r)
        continue
    if not valid_email(r[iE]):
        invalid.append(r)
        continue
    ammo_all.append(r)

print("raw ammo (email present, no sent/failed/excluded/active):", len(ammo_all))
print("invalid-format emails (would be EXCLUDED by pipeline):", len(invalid))
for r in invalid[:12]:
    print("   INVALID:", r[0], "|", (r[iN] or '')[:28], "|", (r[iE] or '')[:50], "|", (r[iS] or '')[:40])
print("active-client rows skipped:", len(excluded_active),
      [(r[0], (r[iN] or '')[:22]) for r in excluded_active[:8]])

# ---- full-file normalized dupes ----
seen = {}
dupes = []
for r in rows[1:]:
    e = norm_email(r[iE]) if len(r) > iE and r[iE].strip() else ''
    if not e:
        continue
    if e in seen:
        dupes.append((seen[e], r[0], e))
    else:
        seen[e] = r[0]
print("duplicate normalized emails in file:", len(dupes), dupes[:10])

# ---- QA on the wave day6_pipeline would fire ----
wave = ammo_all[:100]
flags = []
for r in wave:
    name = (r[iN] or '').strip()
    email = norm_email(r[iE])
    dom = email.split('@')[1] if '@' in email else ''
    local = email.split('@')[0] if '@' in email else ''
    reasons = []
    nl = re.sub(r'[^a-z0-9]', '', name.lower())
    if name.lower() in PLACEHOLDER_NAMES or len(nl) < 5:
        reasons.append('placeholder-name')
    if '@pec.it' in dom or re.match(r'^[a-z]+[a-z0-9]*\d{2,4}@', local) and dom.endswith('pec.it'):
        reasons.append('pec-concat')
    if any(f in dom for f in FED_DOMAINS):
        reasons.append('federation-domain')
    if dom in GENERIC:
        reasons.append('generic-webmail')
    if any(x in dom for x in ('example.com', 'mysite.com', 'ilmiosito.com', 'domain.com',
                              'yourdomain', 'sentry.io', 'wixpress', 'godaddy', 'squarespace')):
        reasons.append('placeholder-domain')
    if not re.search(r'[a-z]', name) or re.fullmatch(r'[\d\s\W]+', name or ''):
        reasons.append('non-name')
    if reasons:
        flags.append((r[0], name[:34], email[:42], r[iC] or '?', ','.join(reasons)))

print("\n=== WAVE (first 100 as pipeline would send) countries ===")
print(dict(Counter((r[iC] or '?').strip() or '?' for r in wave)))
print("\n=== FLAGGED rows in wave:", len(flags), "===")
for f in flags:
    print("  FLAG", f[0], "|", f[1], "|", f[2], "|", f[3], "|", f[4])

print("\n=== first 12 wave rows ===")
for r in wave[:12]:
    print("  ", r[0], "|", (r[iN] or '')[:30], "|", norm_email(r[iE])[:42], "|", r[iC] or '?', "|", (r[iS] or '')[:36])
print("=== last 5 wave rows ===")
for r in wave[-5:]:
    print("  ", r[0], "|", (r[iN] or '')[:30], "|", norm_email(r[iE])[:42], "|", r[iC] or '?', "|", (r[iS] or '')[:36])

# ---- WA candidates (mobile-only, fresh) ----
MOBILE_PREFIX = {'UK': ['447'], 'Spain': ['346', '347'], 'Portugal': ['3519'],
                 'Italy': ['393'], 'Ireland': ['3538'], 'Netherlands': ['316'],
                 'Germany': ['4915', '4916', '4917'], 'France': ['336', '337']}
WA_DONE = ['whatsapp sent', 'wa sent', 'wa=', '"ok":true', 'not on whatsapp',
           "isn't on whatsapp", 'no-composer', 'wa err', 'wa failed', 'wa-pending',
           'whatsapp-only', 'wa numbers banked', 'wa-not']
def norm_phone(p, country):
    p = re.sub(r'[^\d+]', '', (p or '').strip())
    if not p: return ''
    if p.startswith('0'): p = '44' + p[1:]
    if not p.startswith('+'): p = '+' + p
    if len(re.sub(r'\D', '', p)) < 11: return ''
    return p
wa_c = []
for r in rows[1:]:
    if len(r) <= iS: continue
    st = (r[iS] or '').lower()
    if any(p in (r[iN] or '').lower() for p in PERSONAL): continue
    if any(m in st for m in WA_DONE): continue
    if any(m in st for m in ACTIVE): continue
    if any(m in st for m in FED): continue
    ph = norm_phone(r[iP], r[iC])
    if not ph: continue
    mob = MOBILE_PREFIX.get(r[iC] or '')
    if not mob: continue
    if not any(re.sub(r'\D', '', ph).startswith(x) for x in mob): continue
    fresh = ('day 8' in st or 'day 9' in st or 'gmaps' in st or 'daily' in st)
    wa_c.append((0 if fresh else 1, r[0], (r[iN] or '')[:24], ph, r[iC] or '?'))
wa_c.sort(key=lambda x: x[0])
print("\n=== WA mobile candidates:", len(wa_c), "===")
for c in wa_c[:14]:
    print("   ", c)

# ---- IG candidates ----
JUNK_IG = ['squarespace', 'wix', 'jiujitsudotcom', 'embed', 'instagram', 'facebook',
           'wordpress', 'google', 'youtube', 'mail.', 'tiptoe', 'gymshark']
IG_DONE = ['ig follow', 'follow=', 'followed', 'dm=', 'dm sent', 'ig dm', 'ig not found',
           'notfound', 'profile-not-found', 'ig=', 'ig profile not found']
ig_c = []
for r in rows[1:]:
    if len(r) <= iS: continue
    st = (r[iS] or '').lower()
    h = (r[iIG] or '').strip().lstrip('@')
    if not h or h.lower() in JUNK_IG: continue
    if any(m in st for m in IG_DONE): continue
    if any(m in st for m in FED): continue
    fresh = 'gmaps' in st or 'daily' in st
    ig_c.append((0 if fresh else 1, r[0], (r[iN] or '')[:26], h))
ig_c.sort(key=lambda x: x[0])
print("\n=== IG candidates:", len(ig_c), " fresh:", sum(1 for c in ig_c if c[0] == 0), "===")
for c in ig_c[:14]:
    print("   ", c)
