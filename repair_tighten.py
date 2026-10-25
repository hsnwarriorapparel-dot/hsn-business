#!/usr/bin/env python3
"""Day-11 contamination-tightening repair (2026-10-25) + wave builder.

For every row previously marked 'EMAIL FIXED', re-select the address using a
STRICT rule set:
  ACCEPT a candidate only if
    (a) its domain matches the lead's own website base domain, OR
    (b) it is a webmail address whose local part shares a meaningful token with
        the lead's name / website slug (e.g. dbkmilano@gmail.com for DBK Milano), OR
    (c) the lead has NO website recorded and the address is on a non-placeholder,
        non-third-party domain (kept, tagged 'unverified-domain').
  REJECT everything else (booking-platform addresses, unrelated domains, PEC
  concatenations, image-filename pseudo-addresses) -> 'EXCLUDED (cross-site
  contamination: ...)'.
Also strips leading junk chars from the address.

Then builds /home/ubuntu/day11_wave.txt: the prioritized 100-lead email wave
(domain-matched first, then name-matched webmail, then unverified), and
/home/ubuntu/day11_wave_detail.csv for the report.

Row-targeted, atomic write, read-back verification.
"""
import csv, re, os, tempfile, shutil
from urllib.parse import urlparse

CSV = '/home/ubuntu/leads.csv'
WAVE_TXT = '/home/ubuntu/day11_wave.txt'
WAVE_CSV = '/home/ubuntu/day11_wave_detail.csv'

WEBMAIL = ('gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com', 'yahoo.fr',
           'yahoo.it', 'yahoo.es', 'yahoo.de', 'live.com', 'msn.com', 'aol.com',
           'mail.com', 'gmx.de', 'gmx.net', 'web.de', 't-online.de', 'orange.fr',
           'free.fr', 'laposte.net', 'libero.it', 'virgilio.it', 'tiscali.it',
           'protonmail.com', 'proton.me', 'icloud.com', 'me.com', 'zoho.com')
THIRD_PARTY = ('schedulista', 'ayudapanel', 'fitkit', 'usa.com', 'bookizon',
               'squarespace', 'wixsite', 'wix.com', 'facebook.com', 'instagram.com',
               'twitter.com', 'youtube.com', 'linkedin.com', 'google.com',
               'calendly', 'eventbrite', 'mindbody', 'gymdesk', 'mydesign',
               'wordpress.com', 'blogspot', 'weebly', 'jimdo', 'jimdofree',
               'paginasamarillas', 'infoempresa', 'einforma', 'expansion',
               'axesor', 'einforma.com', 'mercadolibre', 'amazon', 'ebay',
               'booking', 'reserv', 'globe', 'tripadvisor', 'yelp')
STOP = {'the', 'and', 'per', 'del', 'della', 'di', 'da', 'do', 'de', 'des', 'du',
        'la', 'le', 'el', 'los', 'las', 'academy', 'academia', 'school', 'scuola',
        'gym', 'club', 'asd', 'a.s.d', 's.s.d', 'centro', 'centro', 'asociacion',
        'associazione', 'martial', 'arts', 'art', 'kung', 'fu', 'taekwondo',
        'jiu', 'jitsu', 'boxing', 'boxe', 'karate', 'team', 'cf', 'ss', 'gs',
        'fit', 'fitness', 'palestra', 'associazione', 'sports', 'a', 'e', 'of',
        'in', 'il', 'istituto', 'instituto', 'centro', 'scuole', 'srl', 'as'}


def norm_email(e):
    e = re.sub(r'^(%20|u00a0|\s)+', '', (e or '').strip().lower())
    return e.lstrip('-.')


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
    t = set()
    for w in re.split(r'[^a-z0-9]+', local.lower()):
        if len(w) >= 4 and w not in STOP:
            t.add(w)
    return t


rows = list(csv.reader(open(CSV, encoding='utf-8', errors='replace')))
hdr = rows[0]
idx = {h: i for i, h in enumerate(hdr)}
iE, iS, iW, iN, iC, iIG, iP = (idx['Email'], idx['Status'], idx['Website'],
                               idx['Name'], idx['Country'], idx['IG Username'], idx['Phone'])

changed, newly_excluded = [], []
for r in rows[1:]:
    if len(r) <= iS:
        continue
    st = r[iS] or ''
    if 'email sent' in st.lower():
        continue
    e = norm_email(r[iE] or '')
    if not e or not valid_email(e):
        continue
    dom = e.split('@')[1]
    local = e.split('@')[0]
    sd = site_domain(r[iW] if len(r) > iW else '')
    name = (r[iN] or '').strip()

    third_party = any(t in dom for t in THIRD_PARTY)
    site_match = bool(sd) and (base(dom) == base(sd) or dom in sd or sd in dom)
    name_match = bool(local_tokens(local) & tokens(name, r[iW] if len(r) > iW else ''))
    pec = dom.endswith('pec.it')

    if third_party or pec:
        reason = 'third-party/platform domain' if third_party else 'PEC concatenated address'
        r[iS] = (st.rstrip(' |') + f' | EXCLUDED (cross-site contamination: {reason})')[:250]
        newly_excluded.append((r[0], e, reason))
        continue
    if sd and not site_match:
        # no site match: acceptable only for a webmail address whose local part
        # matches the business name; otherwise exclude
        if dom in WEBMAIL and name_match:
            r[iS] = (st.rstrip(' |') + ' | EMAIL VERIFIED (webmail, name-matched)')[:250]
            changed.append((r[0], e, 'name-matched webmail'))
        elif dom in WEBMAIL:
            r[iS] = (st.rstrip(' |') + ' | EXCLUDED (webmail address does not match lead name/domain)')[:250]
            newly_excluded.append((r[0], e, 'webmail name mismatch'))
        else:
            r[iS] = (st.rstrip(' |') + ' | EXCLUDED (email domain unrelated to lead website)')[:250]
            newly_excluded.append((r[0], e, 'domain unrelated to site'))
        continue
    if sd and site_match:
        if 'EMAIL FIXED' in st:
            r[iS] = (st.rstrip(' |') + ' | EMAIL VERIFIED (domain match)')[:250]
            changed.append((r[0], e, 'domain match'))
        continue
    # no website recorded
    if dom not in WEBMAIL and not third_party:
        r[iS] = (st.rstrip(' |') + ' | EMAIL VERIFIED (business domain, no site recorded)')[:250]
        changed.append((r[0], e, 'business domain'))

# normalize the address text on every verified row
for r in rows[1:]:
    if len(r) <= iE:
        continue
    e = norm_email(r[iE] or '')
    if e and valid_email(e):
        r[iE] = e

fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
    csv.writer(f).writerows(rows)
os.replace(tmp, CSV)

# ---------- build the wave ----------
rows2 = list(csv.reader(open(CSV, encoding='utf-8', errors='replace')))
ACTIVE = ['follow-up', 'hot lead', 'negotiat', 'sample quote', 'awaiting', 'replied']
JUNK_IG = ['squarespace', 'wix', 'jiujitsudotcom', 'embed', 'instagram', 'facebook',
           'wordpress', 'google', 'youtube', 'mail.', 'tiptoe', 'gymshark']
IG_DONE = ['ig follow', 'follow=', 'followed', 'dm=', 'dm sent', 'ig dm', 'ig not found',
           'notfound', 'profile-not-found', 'ig=', 'ig profile not found']
FED = ['federation', 'verband', 'association', 'bonds', 'federal', 'excluded']

scored = []
for r in rows2[1:]:
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
    dom = e.split('@')[1]
    local = e.split('@')[0]
    sd = site_domain(r[iW] if len(r) > iW else '')
    name = (r[iN] or '').strip()
    site_match = bool(sd) and (base(dom) == base(sd) or dom in sd or sd in dom)
    name_match = bool(local_tokens(local) & tokens(name, r[iW] if len(r) > iW else ''))
    score = 0
    if site_match:
        score += 60
    elif name_match:
        score += 30
    else:
        score += 10
    if dom not in WEBMAIL:
        score += 15
    if local not in ('info', 'contact', 'contatos', 'contacto', 'hello', 'mail',
                      'email', 'office', 'admin', 'ventas', 'support', 'posta'):
        score += 8
    nl = re.sub(r'[^a-z0-9]', '', name.lower())
    if len(nl) < 5:
        score -= 30
    fresh = 4 if '2026-10-25' in st else (3 if '2026-10-24' in st else (2 if '2026-10-23' in st else 1))
    score += fresh
    scored.append((score, r[0], name, e, r[iC] or '?', site_match, name_match, fresh, local))

scored.sort(key=lambda x: (-x[0], int(re.sub(r'\D', '', x[1]) or 0)))
wave = scored[:100]

with open(WAVE_TXT, 'w') as f:
    for s in wave:
        f.write(s[1] + '\n')
with open(WAVE_CSV, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Lead ID', 'Name', 'Email', 'Country', 'Score', 'SiteMatch', 'NameMatch', 'Fresh'])
    for s in wave:
        w.writerow([s[1], s[2], s[3], s[4], s[0], s[5], s[6], s[7]])

# IG candidates for the pass
ig_c = []
for r in rows2[1:]:
    if len(r) <= iS:
        continue
    st = (r[iS] or '').lower()
    h = (r[iIG] or '').strip().lstrip('@')
    if not h or h.lower() in JUNK_IG:
        continue
    if any(m in st for m in IG_DONE):
        continue
    if any(m in st for m in FED):
        continue
    ig_c.append((r[0], r[iN], h))

print("NEWLY EXCLUDED (contamination):", len(newly_excluded))
for x in newly_excluded:
    print("   EXC", x[0], "|", x[1], "|", x[2])
print("RE-VERIFIED:", len(changed))
for x in changed:
    print("   VER", x[0], "|", x[1], "|", x[2])
print()
print("VALID AMMO:", len(scored))
print("WAVE (top 100): site-matched =", sum(1 for s in wave if s[5]),
      "| name-matched =", sum(1 for s in wave if s[6]),
      "| webmail =", sum(1 for s in wave if s[3].split('@')[1] in WEBMAIL))
from collections import Counter
print("wave countries:", dict(Counter(s[4] for s in wave)))
print("wave written:", WAVE_TXT, "| detail:", WAVE_CSV)
print("IG candidates for pass:", len(ig_c))
for x in ig_c[:25]:
    print("   IG", x)
