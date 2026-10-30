#!/usr/bin/env python3
"""Day-15 (2026-10-29) site-verification pass for the ammo pool.

Same ground-truth rule as Day-12/13: fetch each ammo lead's OWN website +
contact pages and confirm the candidate email literally appears on that lead's
pages. ON-SITE -> safe to email. Not on site -> fall back to the strict domain
rule in the wave builder.
Read-only on leads.csv; writes /home/ubuntu/day15_site_verify.csv
"""
import csv, re, sys, json, time
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

CSV = '/home/ubuntu/leads.csv'
OUT = '/home/ubuntu/day15_site_verify.csv'
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'


def fetch(url, timeout=12):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(400000)
            cs = r.headers.get_content_charset()
            return raw.decode(cs, errors='replace') if cs else raw.decode('utf-8', errors='replace')
    except Exception:
        return ''


def norm_email(e):
    return re.sub(r'^(%20|u00a0|u003e|\s)+', '', (e or '').strip().lower()).lstrip('-.')


rows = list(csv.DictReader(open(CSV, newline='', encoding='utf-8')))
cands = []
for r in rows:
    st = (r.get('Status') or '').lower()
    e = norm_email(r.get('Email') or '')
    if not e:
        continue
    if 'email sent' in st or 'failed' in st or 'excluded' in st or 're-hunt' in st:
        continue
    if any(m in st for m in ('follow-up', 'hot lead', 'negotiat', 'sample quote', 'awaiting', 'replied')):
        continue
    if not (r.get('Website') or '').strip():
        continue
    cands.append(r)

print('candidates with website:', len(cands), flush=True)


def check(r):
    site = r['Website'].strip()
    if not site.startswith('http'):
        site = 'https://' + site
    base = site.rstrip('/')
    urls = [base, base + '/contact', base + '/contact-us', base + '/kontakt',
            base + '/impressum', base + '/about', base + '/']
    e = norm_email(r['Email'])
    found = False
    pages = 0
    for u in urls:
        html = fetch(u)
        if not html:
            continue
        pages += 1
        low = html.lower()
        if e in low:
            found = True
            break
        at = e.split('@')[0]
        dom = e.split('@')[1]
        if (at + ' [at] ' + dom) in low or (at + ' (at] ' + dom) in low or \
           (at + ' [at]' + dom) in low or (at + ' (at) ' + dom) in low or \
           (at + '@' + dom.replace('.', '[.]')) in low:
            found = True
            break
        if pages >= 3:
            break
    return (r['Lead ID'], r['Name'][:40], e, r['Website'][:60],
            'ON-SITE' if found else 'not-on-site', pages)


results = []
with ThreadPoolExecutor(max_workers=8) as ex:
    for i, res in enumerate(ex.map(check, cands), 1):
        results.append(res)
        if i % 20 == 0:
            print('  checked', i, '/', len(cands), flush=True)

with open(OUT, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Lead ID', 'Name', 'Email', 'Website', 'Result', 'PagesFetched'])
    for r in results:
        w.writerow(r)

onsite = [r for r in results if r[4] == 'ON-SITE']
print('checked:', len(results), '| found ON their own site:', len(onsite), flush=True)
print('write:', OUT, flush=True)
