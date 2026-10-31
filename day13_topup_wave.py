#!/usr/bin/env python3
"""Build a Day-13 TOP-UP wave: replace the 3 bounced sends so the day lands
on exactly 100 delivered emails. Uses the same QA rules as the main wave
(site verification, junk-name, federation/third-party/placeholder sweeps,
per-business-domain cap) and EXCLUDES any lead whose email was already sent
or bounced today. Writes /home/ubuntu/day13_topup_wave.txt.
"""
import csv, re, os, tempfile
from urllib.parse import urlparse
from collections import Counter

CSV = '/home/ubuntu/leads.csv'
VERIFY = '/home/ubuntu/day13_site_verify.csv'
OUT = '/home/ubuntu/day13_topup_wave.txt'
DETAIL = '/home/ubuntu/day13_topup_detail.csv'
N = 3
DAY = '2026-10-27'

WEBMAIL = ('gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com', 'yahoo.fr',
           'yahoo.it', 'yahoo.es', 'yahoo.de', 'live.com', 'msn.com', 'aol.com',
           'mail.com', 'gmx.de', 'gmx.net', 'web.de', 't-online.de', 'orange.fr',
           'free.fr', 'laposte.net', 'libero.it', 'virgilio.it', 'tiscali.it',
           'protonmail.com', 'proton.me', 'icloud.com', 'me.com', 'zoho.com',
           'outlook.fr', 'outlook.it', 'outlook.de', 'wanadoo.fr', 'telenet.be',
           'skynet.be', 'home.nl', 'kpnmail.nl', 'ziggo.nl', 'planet.nl',
           'wp.pl', 'o2.pl', 'onet.pl', 'interia.pl', 'gazeta.pl', 'wp.com')
FED_DOMAINS = ('ffjudo', 'ffkarate', 'fijlkam', 'judobund', 'wako', 'britishjudo',
               'ffboxe', 'kickboxen-deutschland', 'fkb.nl', 'usaboxing',
               'trouver-un-club', 'kombazen', 'ffsavate', 'ijf.org', 'ifaw',
               'teamusa', 'yelp', 'tripadvisor', 'classpass', 'meetup',
               'yellowpages', 'reddit', 'wikipedia', 'linkedin', 'facebook',
               'instagram', 'youtube', 'tiktok')
THIRD_PARTY = ('schedulista', 'ayudapanel', 'fitkit', 'squarespace', 'wixsite',
               'wix.com', 'google.com', 'calendly', 'eventbrite', 'mindbody',
               'gymdesk', 'wordpress.com', 'blogspot', 'weebly', 'jimdo',
               'sentry', 'wixpress', 'framer', 'webador', 'site123')
PLACEHOLDER_DOMAINS = ('beispiel', 'example.com', 'email.com', 'domain.com',
                       'dominio.com', 'dominio.pt', 'mysite.com', 'test.com',
                       'sample.com', 'yourdomain', 'mydomain', 'exemplo',
                       'exemple', 'placeholder', 'mustermann', 'dummy')
JUNK_NAME = re.compile(r'^(unknown|n/?a|none|null|info|contact|contactos|contacto|'
                        r'kontakt|contatti|where|test|default|xyz|lorem|asdf|xxxx+)\b', re.I)
ACTIVE = ['follow-up', 'hot lead', 'negotiat', 'sample quote', 'awaiting', 'replied']
PERSONAL = ('sayyam', 'shamas', 'afzal', 'chacho nadeem')


def norm_email(e):
    return re.sub(r'^(%20|u00a0|u003e|\s)+', '', (e or '').strip().lower()).lstrip('-.')


def valid_email(e):
    if not re.match(r'^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$', e):
        return False
    dom = e.split('@')[1]
    if re.search(r'\.(jpg|jpeg|png|gif|webp|svg|pdf|html?|css|js|mp4|mp3)$', dom):
        return False
    return '2x' not in dom


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


onsite = {}
if os.path.exists(VERIFY):
    for v in csv.DictReader(open(VERIFY, newline='', encoding='utf-8')):
        onsite[v['Lead ID']] = v['Result'] == 'ON-SITE'

rows = list(csv.reader(open(CSV, encoding='utf-8-sig', errors='replace')))
idx = {h: i for i, h in enumerate(rows[0])}
iE, iS, iW, iN, iC = (idx['Email'], idx['Status'], idx['Website'], idx['Name'], idx['Country'])

first_seen = {}
for r in rows[1:]:
    if len(r) <= iE:
        continue
    e = norm_email(r[iE] or '')
    if e and valid_email(e) and e not in first_seen:
        first_seen[e] = r[0]

cands = []
for r in rows[1:]:
    if len(r) <= iS:
        continue
    st = r[iS] or ''
    sl = st.lower()
    e = norm_email(r[iE] or '')
    if not e or not valid_email(e):
        continue
    if 'email sent' in sl or 'failed' in sl or 'excluded' in sl or 're-hunt' in sl:
        continue
    if any(m in sl for m in ACTIVE):
        continue
    name = (r[iN] or '').strip()
    if any(p in name.lower() for p in PERSONAL):
        continue
    alnum = re.sub(r'[^a-z0-9]', '', name.lower())
    if JUNK_NAME.match(name) or len(alnum) < 4:
        continue
    dom = e.split('@')[1]
    if any(f in dom for f in FED_DOMAINS) or any(t in dom for t in THIRD_PARTY):
        continue
    if any(p in dom for p in PLACEHOLDER_DOMAINS) or dom.endswith('pec.it'):
        continue
    if ',' in e or ' ' in e:
        continue
    sd = site_domain(r[iW] if len(r) > iW else '')
    site_match = bool(sd) and (base(dom) == base(sd) or dom in sd or sd in dom)
    if not (site_match or onsite.get(r[0], False)):
        continue
    if first_seen.get(e) != r[0]:
        continue
    cands.append((0 if '2026-10-27' in sl else 1, r[0], name, e,
                  (r[iC] if len(r) > iC else '') or '', dom))

cands.sort()
per_dom = Counter()
wave = []
for c in cands:
    if c[5] not in WEBMAIL:
        if per_dom[c[5]] >= 4:
            continue
        per_dom[c[5]] += 1
    wave.append(c)
    if len(wave) >= N:
        break

with open(OUT, 'w') as f:
    for c in wave:
        f.write(c[1] + '\n')
with open(DETAIL, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Lead ID', 'Name', 'Email', 'Country', 'Domain'])
    for c in wave:
        w.writerow([c[1], c[2], c[3], c[4], c[5]])

print('top-up candidates scored:', len(cands), '| selected:', len(wave))
for c in wave:
    print('  TOPUP', c[1], '|', c[2][:30], '|', c[3][:40], '|', c[4])
print('written', OUT)
