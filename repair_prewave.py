#!/usr/bin/env python3
"""Day-11 pre-wave CSV repair (2026-10-25):
 1. Malformed Email cells (comma/semicolon-separated lists, scrape junk) -> keep FIRST
    genuinely valid address; if none valid -> mark 'EXCLUDED (reason)' so the wave
    skips them instead of burning quota.
 2. Duplicate normalized emails -> keep the first row, EXCLUDE the later duplicate.
Row-targeted, atomic write, read-back verification. Never touches a row already sent.
"""
import csv, re, os, tempfile, shutil
from collections import Counter

CSV = '/home/ubuntu/leads.csv'
BAK = '/home/ubuntu/leads_prewave_backup_2026-10-25.csv'

GENERIC_BAD = ('sentry-next.wixpress', 'wixpress.com', 'example.com', 'mysite.com',
               'ilmiosito.com', 'yourdomain', 'domain.com', 'sentry.io')
FED_DOMAINS = ('ffjudo', 'ffkarate', 'fijlkam', 'judobund', 'wako', 'britishjudo',
               'ffboxe', 'kickboxen-deutschland', 'fkb.nl', 'usaboxing', 'trouver-un-club',
               'kombazen', 'ffsavate', 'ifbb', 'ibaf', 'teamusa', 'ijf.org')

def norm_email(e):
    return re.sub(r'^(%20|u00a0|\s)+', '', (e or '').strip().lower())

def valid_email(e):
    e = norm_email(e)
    return bool(re.match(r'^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$', e)) and 'http' not in e

def is_junk(e):
    e = norm_email(e)
    return any(b in e for b in GENERIC_BAD) or any(f in e for f in FED_DOMAINS)

shutil.copy2(CSV, BAK)
rows = list(csv.reader(open(CSV, encoding='utf-8', errors='replace')))
hdr = rows[0]
idx = {h: i for i, h in enumerate(hdr)}
iE, iS = idx['Email'], idx['Status']

# ---------- pass 1: repair malformed email cells ----------
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
    if valid_email(raw) and not is_junk(raw):
        continue
    # split into candidates
    parts = [p.strip() for p in re.split(r'[,;\s]+|\s{2,}', raw) if p.strip()]
    good = [p for p in parts if valid_email(p) and not is_junk(p)]
    if good:
        r[iE] = norm_email(good[0])
        r[iS] = (st.rstrip(' |') + ' | EMAIL FIXED (multi-address cell -> first valid)')[:250]
        repaired.append((r[0], raw[:48], norm_email(good[0])))
    else:
        reason = 'scrape-junk/wixpress' if any(b in norm_email(raw) for b in GENERIC_BAD) else 'no valid address in cell'
        r[iS] = (st.rstrip(' |') + f' | EXCLUDED (malformed email cell: {reason})')[:250]
        excluded_bad.append((r[0], raw[:48], reason))

# ---------- pass 2: duplicate normalized emails (later row excluded) ----------
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

# ---------- read-back verification ----------
rows2 = list(csv.reader(open(CSV, encoding='utf-8', errors='replace')))
iE2, iS2 = idx['Email'], idx['Status']
ammo = 0
bad_still = 0
for r in rows2[1:]:
    if len(r) <= iS2:
        continue
    st = (r[iS2] or '').lower()
    if not (r[iE2] or '').strip():
        continue
    if 'email sent' in st or 'failed' in st or 'excluded' in st or 're-hunt' in st:
        continue
    if any(m in st for m in ['follow-up', 'hot lead', 'negotiat', 'sample quote', 'awaiting', 'replied']):
        continue
    if not valid_email(r[iE2]):
        bad_still += 1
        continue
    ammo += 1

print("rows on disk:", len(rows2) - 1)
print("REPAIRED (multi-address cell -> first valid):", len(repaired))
for x in repaired:
    print("   FIX ", x[0], "|", x[1], "->", x[2])
print("EXCLUDED (no valid address):", len(excluded_bad))
for x in excluded_bad:
    print("   EXC ", x[0], "|", x[1], "|", x[2])
print("EXCLUDED (duplicate email):", len(dupes))
for x in dupes:
    print("   DUP ", x[0], "| dup of", x[1], "|", x[2])
print("VALID AMMO after repair:", ammo, "| still-invalid:", bad_still)
print("backup:", BAK)
