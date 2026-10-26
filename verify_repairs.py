#!/usr/bin/env python3
"""Verify the 34 repaired rows: does the chosen email domain match the lead's own
website domain? A mismatch = possible cross-site scrape contamination.
Read-only."""
import csv, re
from urllib.parse import urlparse

CSV = '/home/ubuntu/leads.csv'
rows = list(csv.reader(open(CSV, encoding='utf-8', errors='replace')))
idx = {h: i for i, h in enumerate(rows[0])}
iE, iS, iW, iN = idx['Email'], idx['Status'], idx['Website'], idx['Name']


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


mismatch = []
for r in rows[1:]:
    if len(r) <= iS:
        continue
    if 'EMAIL FIXED' not in (r[iS] or ''):
        continue
    e = (r[iE] or '').strip().lower()
    dom = e.split('@')[1] if '@' in e else ''
    sd = site_domain(r[iW] if len(r) > iW else '')
    ok = bool(sd) and (base(dom) == base(sd) or dom in sd or sd in dom)
    print(f"{'OK  ' if ok else 'DIFF'} {r[0]:6} | {(r[iN] or '')[:28]:28} | {e[:40]:40} | site={sd[:32]}")
    if not ok:
        mismatch.append(r[0])

print("\nMISMATCHED repaired rows:", len(mismatch), mismatch)

print("\n=== emails with leading/trailing junk chars ===")
for r in rows[1:]:
    e = (r[iE] or '').strip()
    if e and (e[0] in '-.' or e[-1] in '-.'):
        print("  ", r[0], repr(e[:50]))
