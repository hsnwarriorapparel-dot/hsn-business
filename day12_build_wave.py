#!/usr/bin/env python3
"""Day-12 (2026-10-26) pre-wave QA + wave builder (v2).

Fixes vs v1:
  - uppercase lead names are NOT junk (the old regex was case-sensitive on the
    alnum-length check and mis-flagged 3 valid gyms)
  - email validity uses the ON-SITE verification result from
    day12_site_verify.csv (the address literally appears on the lead's own
    website) -> accepted even when the domain differs
  - per-domain cap (max 4 emails per company domain) so one chain (Brooklyn
    Fitboxing) cannot eat the wave
  - placeholder-domain sweep (beispiel/example/mustermann/dummy/...)

Writes /home/ubuntu/day12_wave.txt (top 100) + day12_wave_detail.csv and
applies the EXCLUDED status to rejected rows (row-targeted, atomic, read-back).
"""
import csv, re, os, sys, tempfile
from urllib.parse import urlparse
from collections import Counter

CSV = '/home/ubuntu/leads.csv'
VERIFY = '/home/ubuntu/day12_site_verify.csv'
WAVE_TXT = '/home/ubuntu/day12_wave.txt'
WAVE_CSV = '/home/ubuntu/day12_wave_detail.csv'
MAX_PER_DOMAIN = 4

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
           'gmx.net', 'comcast.net', 'verizon.net', 'att.net', 'cox.net',
           'charter.net', 'sbcglobal.net', 'bellsouth.net', 'earthlink.net')

FED_DOMAINS = ('ffjudo', 'ffkarate', 'fijlkam', 'judobund', 'judo-bund',
               'wako', 'britishjudo', 'ffboxe', 'kickboxen-deutschland',
               'kickboxendeutschland', 'fkb.nl', 'usaboxing', 'trouver-un-club',
               'kombazen', 'ffsavate', 'ijf.org', 'ifaw', 'ufi', 'ibsa', 'imaf',
               'olympics.com', 'olympedia', 'teamusa', 'yelp', 'tripadvisor',
               'classpass', 'meetup', 'yellowpages', 'reddit', 'wikipedia',
               'linkedin', 'facebook', 'instagram', 'youtube', 'tiktok')

THIRD_PARTY = ('schedulista', 'ayudapanel', 'fitkit', 'usa.com', 'bookizon',
               'squarespace', 'wixsite', 'wix.com', 'facebook.com', 'instagram.com',
               'twitter.com', 'youtube.com', 'linkedin.com', 'google.com',
               'calendly', 'eventbrite', 'mindbody', 'gymdesk', 'mydesign',
               'wordpress.com', 'blogspot', 'weebly', 'jimdo', 'jimdofree',
               'paginasamarillas', 'infoempresa', 'einforma', 'expansion',
               'axesor', 'mercadolibre', 'amazon', 'ebay', 'booking', 'reserv',
               'tripadvisor', 'yelp', 'sentry', 'wixpress', 'framer.website',
               'framer', 'webador', 'site123', 'jimdo', 'mystrikingly')

PLACEHOLDER_DOMAINS = ('beispiel', 'example.com', 'email.com', 'domain.com',
                       'dominio.com', 'dominio.pt', 'mysite.com', 'test.com',
                       'sample.com', 'yourdomain', 'mydomain', 'exemplo',
                       'exemple', 'placeholder', 'mustermann', 'dummy')

PLACEHOLDER_LOCAL = ('user', 'utente', 'utenti', 'example', 'esempio', 'beispiel',
                     'yourname', 'vorname', 'nombre', 'nom', 'email', 'mail',
                     'nome', 'nomeazienda', 'company', 'test', 'demo', 'info')

JUNK_NAME = re.compile(r'^(unknown|n/?a|none|null|info|contact|contactos|contacto|'
                        r'kontakt|contatti|where|test|default|xyz|lorem|asdf|xxxx+)\b', re.I)
STOP = {'the', 'and', 'per', 'del', 'della', 'di', 'da', 'do', 'de', 'des', 'du',
        'la', 'le', 'el', 'los', 'las', 'academy', 'academia', 'school', 'scuola',
        'gym', 'club', 'asd', 'a.s.d', 's.s.d', 'centro', 'asociacion',
        'associazione', 'martial', 'arts', 'art', 'kung', 'fu', 'taekwondo',
        'jiu', 'jitsu', 'boxing', 'boxe', 'karate', 'team', 'cf', 'ss', 'gs',
        'fit', 'fitness', 'palestra', 'sports', 'a', 'e', 'of', 'in', 'il',
        'istituto', 'instituto', 'scuole', 'srl', 'as', 'center', 'centre',
        'dojo', 'kampf', 'combat', 'fighting', 'mma'}


def norm_email(e):
    return re.sub(r'^(%20|u00a0|u003e|\s)+', '', (e or '').strip().lower()).lstrip('-.')


def valid_email(e):
    e = norm_email(e)
    if not re.match(r'^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$', e):
        return False
    if 'http' in e:
        return False
    dom = e.split('@')[1]
    if re.search(r'\.(jpg|jpeg|png|gif|webp|svg|pdf|html?|css|js|mp4|mp3)$', dom):
        return False
    if '2x' in dom:
        return False
    return True


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


def tokens(name, website):
    t = set()
    for src in (name or '', website or ''):
        for w in re.split(r'[^a-z0-9à-ÿ]+', src.lower()):
            if len(w) >= 4 and w not in STOP:
                t.add(w)
                if len(w) > 5:
                    t.add(w[:5])
    return t


def local_tokens(local):
    return {w for w in re.split(r'[^a-z0-9]+', local.lower())
            if len(w) >= 4 and w not in STOP}


onsite = {}
if os.path.exists(VERIFY):
    for v in csv.DictReader(open(VERIFY, newline='', encoding='utf-8')):
        onsite[v['Lead ID']] = v['Result'] == 'ON-SITE'

rows = list(csv.reader(open(CSV, encoding='utf-8-sig', errors='replace')))
hdr = rows[0]
idx = {h: i for i, h in enumerate(hdr)}
iE, iS, iW, iN, iC, iCi = (idx['Email'], idx['Status'], idx['Website'],
                           idx['Name'], idx['Country'], idx['City'])

first_seen = {}
for r in rows[1:]:
    if len(r) <= iE:
        continue
    e = norm_email(r[iE] or '')
    if e and valid_email(e) and e not in first_seen:
        first_seen[e] = (r[0] or '')

ACTIVE = ['follow-up', 'hot lead', 'negotiat', 'sample quote', 'awaiting', 'replied']
scored = []
excluded = []
seen_emails = set()
status_updates = {}

for r in rows[1:]:
    if len(r) <= iS:
        continue
    st = r[iS] or ''
    sl = st.lower()
    e = norm_email(r[iE] or '')
    if not e:
        continue
    if 'email sent' in sl or 'failed' in sl or 'excluded' in sl or 're-hunt' in sl:
        continue
    if any(m in sl for m in ACTIVE):
        continue
    name = (r[iN] or '').strip()
    website = (r[iW] if len(r) > iW else '') or ''
    dom = e.split('@')[1]
    local = e.split('@')[0]

    def ex(reason, mark=True):
        excluded.append((r[0], name, e, reason))
        if mark:
            status_updates[r[0]] = f"EXCLUDED (day12 QA: {reason})"

    if not valid_email(e):
        ex('invalid email format')
        continue
    alnum = re.sub(r'[^a-z0-9]', '', name.lower())
    if JUNK_NAME.match(name) or len(alnum) < 4:
        ex('junk/placeholder lead name')
        continue
    if any(f in dom for f in FED_DOMAINS):
        ex('federation/directory domain')
        continue
    if any(t in dom for t in THIRD_PARTY):
        ex('third-party/platform domain')
        continue
    if any(p in dom for p in PLACEHOLDER_DOMAINS):
        ex('placeholder/example domain')
        continue
    if dom.endswith('pec.it'):
        ex('PEC concatenated address')
        continue
    if local in PLACEHOLDER_LOCAL and dom in WEBMAIL:
        ex('placeholder local part')
        continue
    if ',' in e or ' ' in e:
        ex('multi-address email cell')
        continue

    sd = site_domain(website)
    sbase = base(sd) if sd else ''
    site_match = bool(sd) and (base(dom) == sbase or dom in sd or sd in dom)
    name_match = bool(local_tokens(local) & tokens(name, website))
    verified_onsite = onsite.get(r[0], False)

    if site_match:
        kind = 'site-domain-match'
    elif verified_onsite:
        kind = 'verified-on-own-site'
    elif sd and dom in WEBMAIL and name_match:
        kind = 'webmail-name-match'
    elif not sd and dom not in WEBMAIL:
        kind = 'business-domain-no-site'
    else:
        ex('email not verifiable on the lead own site')
        continue

    if first_seen.get(e) != (r[0] or ''):
        ex('duplicate email (earlier lead already holds it)', mark=False)
        continue
    if e in seen_emails:
        ex('duplicate email within wave', mark=False)
        continue

    score = 0
    score += {'site-domain-match': 60, 'verified-on-own-site': 50,
              'webmail-name-match': 30, 'business-domain-no-site': 12}[kind]
    if dom not in WEBMAIL:
        score += 12
    if local not in ('info', 'contact', 'contatos', 'contacto', 'hello', 'mail',
                     'email', 'office', 'admin', 'ventas', 'support', 'posta'):
        score += 8
    fresh = (4 if '2026-10-26' in st else 3 if '2026-10-25' in st
             else 2 if '2026-10-24' in st else 1 if '2026-10-23' in st else 0)
    score += fresh * 2
    seen_emails.add(e)
    scored.append((score, r[0], name, e, (r[iC] if len(r) > iC else '') or '',
                   kind, fresh, (r[iCi] if len(r) > iCi else '') or '', dom))

scored.sort(key=lambda x: (-x[0], int(re.sub(r'\D', '', x[1]) or 0)))

# per-domain cap
wave = []
per_dom = Counter()
for s in scored:
    if per_dom[s[8]] >= MAX_PER_DOMAIN:
        continue
    per_dom[s[8]] += 1
    wave.append(s)
    if len(wave) >= 100:
        break

# apply EXCLUDED statuses
if status_updates:
    for r in rows[1:]:
        if r[0] in status_updates:
            r[iS] = (r[iS].rstrip(' |') + ' | ' + status_updates[r[0]])[:250]
    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(rows)
    os.replace(tmp, CSV)
    # read-back
    chk = list(csv.reader(open(CSV, encoding='utf-8-sig', errors='replace')))
    print('csv rows after exclusion write:', len(chk) - 1, '| excluded marks applied:', len(status_updates))

with open(WAVE_TXT, 'w') as f:
    for s in wave:
        f.write(s[1] + '\n')
with open(WAVE_CSV, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Lead ID', 'Name', 'Email', 'Country', 'City', 'Score', 'Kind', 'Fresh', 'Domain'])
    for s in wave:
        w.writerow([s[1], s[2], s[3], s[4], s[7], s[0], s[5], s[6], s[8]])

print('VALID AMMO:', len(scored), '| WAVE:', len(wave))
print('QA exclusions:', len(excluded))
print('wave kinds:', dict(Counter(s[5] for s in wave)))
print('wave countries:', dict(Counter(s[4] for s in wave)))
print('wave webmail:', sum(1 for s in wave if s[3].split('@')[1] in WEBMAIL))
print('unique domains in wave:', len(set(s[8] for s in wave)))
print('--- exclusions ---')
for x in excluded:
    print('   EXC', x[0], '|', x[1][:30], '|', x[2][:38], '|', x[3])
print('--- wave sample ---')
for s in wave[:10]:
    print('   WAVE', s[1], '|', s[2][:26], '|', s[3][:36], '|', s[4], '|', s[5])
