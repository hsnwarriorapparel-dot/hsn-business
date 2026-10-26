#!/usr/bin/env python3
"""Day-11 pre-wave CSV repair v2 (2026-10-25):
Pick the BEST address from malformed multi-address cells, not merely the first.
Scoring: reject image-filenames / placeholder domains / generic filler local parts;
prefer the address whose domain matches the lead's own website domain; then prefer
non-webmail domains; then first remaining. Rows with no acceptable address get
'EXCLUDED (reason)' so they never burn email quota.
Also marks later duplicate normalized emails as EXCLUDED.
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

BAD_LOCAL = ('utente', 'user', 'username', 'info', 'contact', 'contacto', 'contatos',
             'hello', 'hi', 'mail', 'email', 'webmaster', 'admin', 'office', 'office@',
             'example', 'test', 'demo', 'nome', 'nombre', 'name', 'support', 'vendas',
             'recepcion', 'ventas', 'segreteria')
BAD_DOMAINS = ('dominio.com', 'domain.com', 'miempresa.es', 'mycompany.es', 'mysite.com',
               'example.com', 'example.org', 'email.com', 'sentry-next.wixpress.com',
               'wixpress.com', 'wix.com', 'sentry.io', 'yoursite.com', 'yoursite.org',
               'sitename.com', 'nombredeempresa.com', 'ilmiosito.com', 'test.com',
               'yourdomain.com', 'sitemail.com', 'asd.com')
FED_DOMAINS = ('ffjudo', 'ffkarate', 'fijlkam', 'judobund', 'wako', 'britishjudo',
               'ffboxe', 'kickboxen-deutschland', 'fkb.nl', 'usaboxing', 'trouver-un-club',
               'kombazen', 'ffsavate', 'ifbb', 'ibaf', 'teamusa', 'ijf.org')

def norm_email(e):
    return re.sub(r'^(%20|u00a0|\s)+', '', (e or '').strip().lower())

def valid_email(e):
    e = norm_email(e)
    if not re.match(r'^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$', e):
        return False
    if 'http' in e:
        return False
    dom = e.split('@')[1]
    if re.search(r'\.(jpg|jpeg|png|gif|webp|svg|pdf|html?|css|js)$', dom):
        return False
    if '2x' in dom or dom.startswith('2x'):
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

def base_dom(dom):
    parts = dom.split('.')
    return '.'.join(parts[-2:]) if len(parts) >= 2 else dom

def hard_reject(e, dom):
    if any(b in dom for b in BAD_DOMAINS):
        return 'placeholder-domain'
    if any(f in dom for f in FED_DOMAINS):
        return 'federation-domain'
    local = e.split('@')[0]
    if local in BAD_LOCAL:
        return 'generic-local-part'
    if len(local) > 45 or '-' in local and len(local) > 30:
        return 'junk-local-part'
    if re.search(r'(mp|jpg|png|2x|share|facebook|youtube|download)', local):
        return 'junk-local-part'
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
    if valid_email(cur) and not hard_reject(cur, cur.split('@')[1]):
        continue
    parts = [p.strip() for p in re.split(r'[,;\s]+', raw) if p.strip()]
    cands = []
    for p in parts:
        e = norm_email(p)
        if not valid_email(e):
            continue
        rej = hard_reject(e, e.split('@')[1])
        if rej:
            continue
        dom = e.split('@')[1]
        sd = site_domain(r[iW] if len(r) > iW else '')
        score = 0
        if sd and (base_dom(dom) == base_dom(sd) or dom in sd or sd in dom):
            score += 100
        if dom not in WEBMAIL:
            score += 20
        cands.append((score, e))
    if cands:
        cands.sort(key=lambda x: -x[0])
        best = cands[0][1]
        r[iE] = best
        r[iS] = (st.rstrip(' |') + ' | EMAIL FIXED (multi-address cell -> best valid)')[:250]
        repaired.append((r[0], raw[:46], best))
    else:
        reason = ('scrape-junk/placeholder' if any(b in norm_email(raw) for b in BAD_DOMAINS)
                  or any('2x' in p or re.search(r'\.(jpg|png)', p, re.I) for p in parts)
                  else 'no acceptable address in cell')
        r[iS] = (st.rstrip(' |') + f' | EXCLUDED (malformed email cell: {reason})')[:250]
        excluded_bad.append((r[0], raw[:46], reason))

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
ammo, bad, webmail_ammo = 0, 0, 0
for r in rows2[1:]:
    if len(r) <= iS:
        continue
    st = (r[iS2] or '').lower() if False else (r[iS] or '').lower()
    e = norm_email(r[iE] or '')
    if not e:
        continue
    if 'email sent' in st or 'failed' in st or 'excluded' in st or 're-hunt' in st:
        continue
    if any(m in st for m in ['follow-up', 'hot lead', 'negotiat', 'sample quote', 'awaiting', 'replied']):
        continue
    if not valid_email(e):
        bad += 1
        continue
    if hard_reject(e, e.split('@')[1]):
        bad += 1
        continue
    ammo += 1
    if e.split('@')[1] in WEBMAIL:
        webmail_ammo += 1

print("rows on disk:", len(rows2) - 1)
print("REPAIRED:", len(repaired))
for x in repaired:
    print("   FIX ", x[0], "|", x[1], "->", x[2])
print("EXCLUDED (no acceptable address):", len(excluded_bad))
for x in excluded_bad:
    print("   EXC ", x[0], "|", x[1], "|", x[2])
print("EXCLUDED (duplicate email):", len(dupes))
for x in dupes:
    print("   DUP ", x[0], "| dup of", x[1], "|", x[2])
print("VALID AMMO after repair:", ammo, "| rejected:", bad,
      "| of which webmail-domain:", webmail_ammo)
