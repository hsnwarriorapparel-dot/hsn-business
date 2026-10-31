#!/usr/bin/env python3
"""Day-13 (2026-10-27) IG handle hunt for the wave leads + fresh gmaps leads.

Rule 3 of the business hub: every lead found gets IG follow + DM on the same
day. gmaps only extracts IG handles from instagram.com links in the website
column (~1/171 yield), so most wave leads have no handle. This script crawls
each lead's own website + contact pages for instagram.com/<handle> links and
writes the handle into leads.csv (row-targeted atomic write).

Read-only except for the IG Username / IG Profile Link columns.
"""
import csv, re, os, sys, tempfile, time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

CSV = '/home/ubuntu/leads.csv'
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'

IG_LINK = re.compile(r'https?://(?:www\.)?instagram\.com/([A-Za-z0-9_.]{2,40})', re.I)
BAD = {'p', 'reel', 'reels', 'explore', 'accounts', 'direct', 'tv', 'stories',
       's', 'about', 'developer', 'business', 'challenge', 'accounts'}


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
iIG, iLINK, iW, iS, iN = (idx['IG Username'], idx['IG Profile Link'], idx['Website'],
                          idx['Status'], idx['Name'])

# targets: wave leads (today) + any lead still missing a handle
wave_ids = set(l.strip() for l in open('/home/ubuntu/day16_wave.txt') if l.strip())
targets = []
for r in rows[1:]:
    if len(r) <= iW:
        continue
    lid = r[0]
    if (r[iIG] or '').strip():
        continue
    if lid not in wave_ids:
        continue
    if not (r[iW] or '').strip():
        continue
    targets.append(r)
print('wave leads missing IG handle:', len(targets), flush=True)


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
            if not h or h.lower() in BAD:
                continue
            if h.lower().startswith('p/'):
                continue
            found.add(h)
        if found:
            break
        if pages >= 3:
            break
    return (r[0], (r[iN] or '')[:30], sorted(found)[:3])


results = []
with ThreadPoolExecutor(max_workers=8) as ex:
    for i, res in enumerate(ex.map(find, targets), 1):
        results.append(res)
        if i % 20 == 0:
            print('  checked', i, '/', len(targets), flush=True)

updates = {}
for lid, name, handles in results:
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
    for lid, (h, link) in list(updates.items())[:15]:
        print('   IG+', lid, '@' + h, flush=True)

print('done. leads with an IG handle discovered:', len(updates), flush=True)
