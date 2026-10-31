#!/usr/bin/env python3
"""Day-13 (2026-10-27) BACKLOG IG handle hunt.

Same as day14_ig_hunt.py but for every lead that still has no IG handle
(not just today's wave) -- each lead must get IG follow+DM the same day it is
found, so the backlog needs handles before its wave day.
Read-only except for the IG Username / IG Profile Link columns.
"""
import csv, re, os, sys, tempfile, time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

CSV = '/home/ubuntu/leads.csv'
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'

IG_LINK = re.compile(r'https?://(?:www\.)?instagram\.com/([A-Za-z0-9_.]{2,40})', re.I)
BAD = {'p', 'reel', 'reels', 'explore', 'accounts', 'direct', 'tv', 'stories',
       's', 'about', 'developer', 'business', 'challenge', 'embed', 'share',
       'plugins', 'static', 'assets', 'widgets'}


def fetch(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(350000)
            cs = r.headers.get_content_charset()
            return raw.decode(cs, errors='replace') if cs else raw.decode('utf-8', errors='replace')
    except Exception:
        return ''


rows = list(csv.reader(open(CSV, encoding='utf-8-sig', errors='replace')))
idx = {h: i for i, h in enumerate(rows[0])}
iIG, iLINK, iW, iS = idx['IG Username'], idx['IG Profile Link'], idx['Website'], idx['Status']

targets = []
for r in rows[1:]:
    if len(r) <= iW:
        continue
    if (r[iIG] or '').strip():
        continue
    if not (r[iW] or '').strip():
        continue
    st = (r[iS] or '').lower()
    if any(m in st for m in ('email sent', 'excluded', 'follow-up', 'hot lead',
                             'negotiat', 'sample quote', 'awaiting', 'replied')):
        continue
    targets.append(r)
print('backlog leads missing IG handle:', len(targets), flush=True)


def find(r):
    site = r[iW].strip()
    if not site.startswith('http'):
        site = 'https://' + site
    base = site.rstrip('/')
    urls = [base, base + '/contact', base + '/contact-us', base + '/kontakt',
            base + '/impressum', base + '/about', base + '/']
    found = set()
    pages = 0
    for u in urls:
        html = fetch(u)
        if not html:
            continue
        pages += 1
        for m in IG_LINK.findall(html):
            h = m.strip().strip('/')
            if not h or h.lower() in BAD or h.lower().startswith('p/'):
                continue
            if '.' in h and not h.lower().endswith(('.shop', '.fit')):
                continue
            found.add(h)
        if found:
            break
        if pages >= 3:
            break
    return (r[0], sorted(found)[:3])


results = []
with ThreadPoolExecutor(max_workers=10) as ex:
    for i, res in enumerate(ex.map(find, targets), 1):
        results.append(res)
        if i % 25 == 0:
            print('  checked', i, '/', len(targets), flush=True)

updates = {}
for lid, handles in results:
    if handles:
        h = handles[0]
        updates[lid] = (h, 'https://instagram.com/' + h)

if updates:
    for r in rows[1:]:
        if r[0] in updates:
            h, link = updates[r[0]]
            r[iIG] = '@' + h
            r[iLINK] = link
    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(rows)
    os.replace(tmp, CSV)
    chk = list(csv.reader(open(CSV, encoding='utf-8-sig', errors='replace')))
    print('csv rows after IG write:', len(chk) - 1, '| IG handles written:', len(updates), flush=True)

print('done. backlog IG handles discovered:', len(updates), flush=True)
