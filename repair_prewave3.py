#!/usr/bin/env python3
"""Day-11 pre-wave CSV repair v3 (2026-10-25) — FINAL.
Rules (conservative: only reject what is provably junk):
  REJECT an address when:
    - the domain is an image/file extension (.jpg/.png/...) or contains '2x'
    - the domain is a known placeholder/parking domain
    - the local part is a known placeholder (utente/user/example/test/demo/asd)
    - the local part looks like a hash, or contains logo/header/share/2x markers
    - the domain is a federation/committee domain
  KEEP everything else, including info@ and contact@ on real business domains.
When a cell holds several addresses, pick the best one:
    +100 domain matches the lead's own website domain
    +30  not a webmail domain (webmail still allowed)
    +10  specific (non-generic) local part
    reject score first, then sort.
Later duplicates of an already-stored normalized email -> EXCLUDED (duplicate).
Row-targeted, atomic write, read-back verification. Never touches an already-sent row.
"""
import csv, re, os, tempfile, shutil
from urllib.parse import urlparse

CSV = '/home/ubuntu/leads.csv'
BAK = '/home/ubuntu/leads_prewave_backup_2026-10-25.csv'

WEBMAIL = ('gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com', 'yahoo.fr',
           'yahoo.it', 'yahoo.es', 'yahoo.de', 'live.com', 'msn.com', 'aol.com',
           'mail.com', 'gmx.de', 'gmx.net', 'web.de', 't-online.de', 'orange.fr',
           'free.fr', 'laposte.net', 'libero.it', 'virgilio.it', 'tiscali.it',
           'protonmail.com', 'proton.me', 'icloud.com', 'me.com', 'zoho.com')

BAD_DOMAINS = ('dominio.com', 'domain.com', 'miempresa.es', 'mycompany.es', 'mysite.com',
               'example.com', 'example.org', 'email.com', 'sentry-next.wixpress.com',
               'wixpress.com', 'sentry.io', 'yoursite.com', 'yoursite.org',
               'sitename.com', 'nombredeempresa.com', 'ilmiosito.com', 'test.com',
               'yourdomain.com', 'sitemail.com', 'sentry.wixpress.com')
FED_DOMAINS = ('ffjudo', 'ffkarate', 'fijlkam', 'judobund', 'wako', 'britishjudo',
               'ffboxe', 'kickboxen-deutschland', 'fkb.nl', 'usaboxing', 'trouver-un-club',
               'kombazen', 'ffsavate', 'ifbb', 'ibaf', 'teamusa', 'ijf.org')
BAD_LOCAL_EXACT = {'utente', 'user', 'username', 'example', 'test', 'demo', 'asd',
                   'nome', 'nombre', 'yourname', 'firstname', 'lastname'}
GENERIC_LOCAL = {'info', 'contact', 'contatos', 'contacto', 'hello', 'hi', 'mail',
                 'email', 'webmaster', 'admin', 'office', 'ventas', 'recepcion',
                 'recepción', 'support', 'kontakt', 'posta', 'posta'}
JUNK_LOCAL_RE = re.compile(r'(2x|logo|header|banner|share-facebook|share-youtube|'
                           r'share-instagram|download|placeholder|sample|image|photo)',
                           re.I)
HASH_LOCAL_RE = re.compile(r'^[0-9a-f]{16,}$', re.I)


def norm_email(e):
    return re.sub(r'^(%20|u00a0|\s)+', '', (e or '').strip().lower())


def valid_email(e):
    e = norm_email(e)
    if not re.match(r'^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$', e):
        return False
    if 'http' in e:
        return False
    dom = e.split('@')[1]
    if re.search(r'\.(jpg|jpeg|png|gif|webp|svg|pdf|html?|css|js|mp4|mp3)$', dom):
        return False
    return True


def site_domain(website):
    w = (website or '').strip()
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


def reject_reason(e):
    dom = e.split('@')[1]
    local = e.split('@')[0]
    if '2x' in dom:
        return 'image-filename-domain'
    if any(b in dom for b in BAD_DOMAINS):
        return 'placeholder-domain'
    if any(f in dom for f in FED_DOMAINS):
        return 'federation-domain'
    if local in BAD_LOCAL_EXACT:
        return 'placeholder-local-part'
    if JUNK_LOCAL_RE.search(local):
        return 'junk-local-part'
    if HASH_LOCAL_RE.match(local):
        return 'hash-local-part'
    if len(local) > 40:
        return 'overlong-local-part'
    return None


shutil.copy2(CSV, BAK)
rows = list(csv.reader(open(CSV, encoding='utf-8', errors='replace')))
hdr = rows[0]
idx = {h: i for i, h in enumerate(hdr)}
iE, iS, iW = idx['Email'], idx['Status'], idx['Website']

repaired, excluded_bad = [], []
for r in rows[1:]:
    if len(r) <= iS:
        continue
    st = (r[iS] or '')
    if 'email sent' in st.lower():
        continue
    raw = (r[iE] or '').strip()
    if not raw:
        continue
    cur = norm_email(raw)
    if valid_email(cur) and not reject_reason(cur):
        continue
    parts = [p.strip() for p in re.split(r'[,;\s]+', raw) if p.strip()]
    cands = []
    for p in parts:
        e = norm_email(p)
        if not valid_email(e) or reject_reason(e):
            continue
        dom = e.split('@')[1]
        local = e.split('@')[0]
        sd = site_domain(r[iW] if len(r) > iW else '')
        score = 0
        if sd and (base_dom(dom) == base_dom(sd) or dom in sd or sd in dom):
            score += 100
        if dom not in WEBMAIL:
            score += 30
        if local not in GENERIC_LOCAL:
            score += 10
        cands.append((score, e))
    if cands:
        cands.sort(key=lambda x: (-x[0], x[1]))
        best = cands[0][1]
        r[iE] = best
        r[iS] = (st.rstrip(' |') + ' | EMAIL FIXED (multi-address cell -> best valid)')[:250]
        repaired.append((r[0], raw[:46], best))
    else:
        r[iS] = (st.rstrip(' |') + ' | EXCLUDED (malformed email cell: no usable address)')[:250]
        excluded_bad.append((r[0], raw[:46], 'no usable address'))

seen = {}
dupes = []
for r in rows[1:]:
    if len(r) <= iS:
        continue
    e = norm_email(r[iE] or '')
    if not e or not valid_email(e):
        continue
    st = (r[iS] or '').lower()
    if 'email sent' in st:
        seen.setdefault(e, r[0])
        continue
    if e in seen:
        r[iS] = ((r[iS] or '').rstrip(' |') + f' | EXCLUDED (duplicate email, first={seen[e]})')[:250]
        dupes.append((r[0], seen[e], e))
    else:
        seen[e] = r[0]

fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
    csv.writer(f).writerows(rows)
os.replace(tmp, CSV)

rows2 = list(csv.reader(open(CSV, encoding='utf-8', errors='replace')))
ammo, rejected, webmail_ammo, first_ids = 0, 0, 0, []
for r in rows2[1:]:
    if len(r) <= iS:
        continue
    st = (r[iS] or '').lower()
    e = norm_email(r[iE] or '')
    if not e:
        continue
    if 'email sent' in st or 'failed' in st or 'excluded' in st or 're-hunt' in st:
        continue
    if any(m in st for m in ['follow-up', 'hot lead', 'negotiat', 'sample quote', 'awaiting', 'replied']):
        continue
    if not valid_email(e) or reject_reason(e):
        rejected += 1
        continue
    ammo += 1
    if e.split('@')[1] in WEBMAIL:
        webmail_ammo += 1
    if len(first_ids) < 100:
        first_ids.append(r[0])

print("rows on disk:", len(rows2) - 1)
print("REPAIRED:", len(repaired))
for x in repaired:
    print("   FIX ", x[0], "|", x[1], "->", x[2])
print("EXCLUDED (no usable address):", len(excluded_bad))
for x in excluded_bad:
    print("   EXC ", x[0], "|", x[1])
print("EXCLUDED (duplicate email):", len(dupes))
for x in dupes:
    print("   DUP ", x[0], "| dup of", x[1], "|", x[2])
print("VALID AMMO:", ammo, "| rejected:", rejected, "| webmail-domain among ammo:", webmail_ammo)
print("wave id range:", first_ids[0] if first_ids else '-', "->", first_ids[-1] if first_ids else '-')
