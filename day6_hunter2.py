#!/usr/bin/env python3
"""Day 6 hunt v2: DuckDuckGo HTML search for gym contact emails (IT/DE/NL/FR)."""
import re, csv, os, tempfile, time, urllib.request, urllib.parse

def fetch(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return ''

def ddg_search(q):
    html = fetch('https://html.duckduckgo.com/html/?q=' + urllib.parse.quote(q))
    if not html:
        return []
    links = re.findall(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html)
    out = []
    for url, title in links[:8]:
        real = re.sub(r'^//duckduckgo com/l/\?uddg=', '', url) if 'uddg' in url else url
        real = urllib.parse.unquote(real.split('&')[0].replace('//duckduckgo.com/l/?uddg=', ''))
        clean = re.sub(r'<[^>]+>', '', title)
        out.append((real, clean))
    return out

# check leads.csv dedupe
def load_existing():
    with open('/home/ubuntu/leads.csv') as f:
        rows = list(csv.reader(f))
    idx = {h: i for i, h in enumerate(rows[0])}
    emails = {r[idx['Email']].strip().lower() for r in rows[1:]}
    phones = {re.sub(r'\D', '', r[idx['Phone']]) for r in rows[1:]}
    return rows, idx, emails, phones

def add_lead(company, email, phone, country, city):
    rows, idx, emails, phones = load_existing()
    if email and email.lower() in emails:
        return None
    if phone and re.sub(r'\D', '', phone) in phones:
        return None
    num = len(rows)
    rows.append([f"L{num:03d}", company, country, city, email, phone, '', '', "Day 6 hunt", '', '', '', '', '', f"Hunted 2026-10-18", '', '', ''])
    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='') as f:
        csv.writer(f).writerows(rows)
    os.replace(tmp, '/home/ubuntu/leads.csv')
    return f"L{num:03d}"

BLOCKED_DOMAINS = ['gmail.com', 'hotmail.com', 'yahoo.com', 'federation', 'ffjudo', 'ffkarate', 'fijlkam', 'judoinside', 'usaboxing', 'wako', 'judobund', 'ffboxe', 'kickboxen-deutschland', 'britishjudo', 'trouver-un-club', 'kombazen', 'ffsavate']
QUERIES = [
    ("Italy", "boxe palestra milano roma contact email site:it -inurl:(login,register)"),
    ("Germany", "boxgym mma kickboxen studio kontakt email impressum -inurl:login"),
    ("Netherlands", "bokschool gym amsterdam contact email boksen"),
    ("France", "club boxe anglaise paris contact email -ffboxe"),
    ("Ireland", "boxing club dublin contact email training"),
    ("UK", "martial arts academy london contact email gear wholesale"),
]
total = 0
for country, q in QUERIES:
    print(f"--- {country} ---", flush=True)
    results = ddg_search(q)
    time.sleep(3)
    for url, title in results[:5]:
        html = fetch(url)
        if not html:
            continue
        emails = [e for e in re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html) 
                  if not any(b in e.lower() for b in BLOCKED_DOMAINS)][:1]
        if not emails:
            continue
        lid = add_lead(title[:40], emails[0], '', country, '')
        if lid:
            total += 1
            print(f"  + {lid} {title[:35]} | {emails[0]}", flush=True)
        time.sleep(2)
print(f"TOTAL NEW: {total}")
