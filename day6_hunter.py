#!/usr/bin/env python3
"""Day 6 prep: hunt fresh EU martial arts gym leads with emails."""
import re, csv, os, tempfile, time, urllib.request

def fetch(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode('utf-8', errors='ignore')
    except Exception:
        return ''

def extract_emails(html):
    return list(dict.fromkeys(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)))

def extract_wa(html):
    m = re.findall(r'(?:wa\.me/|api\.whatsapp\.com/send\?phone=|tel:)(\+?\d[\d\s-]{7,16})', html)
    out = []
    for p in m:
        p2 = re.sub(r'[^\d+]', '', p)
        if len(p2) >= 11:
            out.append(p2)
    return list(dict.fromkeys(out))[:2]

BLOCKED = ['federation', 'ffjudo', 'ffkarate', 'fijlkam', 'judoinside', 'usaboxing', 'fkb.nl', 'wako', 'judobund', 'ffboxe', 'kickboxen-deutschland', 'britishjudo', 'trouver-un-club', 'kombazen', 'ffsavate', 'gmail.com', 'hotmail.com', 'yahoo.com']

def add_lead(company, email, phone, ig, country, city):
    with open('/home/ubuntu/leads.csv') as f:
        rows = list(csv.reader(f))
    idx = {h: i for i, h in enumerate(rows[0])}
    existing_emails = {r[idx['Email']].strip().lower() for r in rows[1:]}
    existing_phones = {re.sub(r'\D', '', r[idx['Phone']]) for r in rows[1:]}
    if email.lower() in existing_emails or re.sub(r'\D', '', phone or '') in existing_phones and phone:
        return 'dup'
    num = len(rows)
    rows.append([f"L{num:03d}", company, country, city, email, phone, ig, '', f"Day 6 hunt", '', '', '', '', '', f"Hunted 2026-10-18", '', '', ''])
    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='') as f:
        csv.writer(f).writerows(rows)
    os.replace(tmp, '/home/ubuntu/leads.csv')
    return f"L{num:03d}"

# Directories of gyms with known contact pages (UK/FR/DE)
SITES = [
    ("https://www.boxinglondon.co.uk/", "UK", "London", "Boxing London"),
    ("https://www.fighting-fitzroy.com/", "UK", "London", "Fighting Fitzroy"),
    ("https://www.kingsbourneboxing.co.uk/", "UK", "London", "Kingsbourne Boxing"),
    ("https://www.londonfightfactory.com/", "UK", "London", "London Fight Factory"),
    ("https://www.mmafactory.fr/", "France", "Paris", "MMA Factory"),
    ("https://www.teamhaas.fr/", "Facebook" in "France" and "France" or "France", "Paris", "Team Haas"),
    ("https://boxingarenanantes.fr/", "France", "Nantes", "Boxing Arena Nantes"),
    ("https://www.boxingclubnantais.com/", "France", "Nantes", "Boxing Club Nantais"),
    ("https://koteam.pt/", "Portugal", "Porto", "KO Team"),
    ("https://www.armazenjiujitsu.com/muaythaimma", "Portugal", "Lisbon", "Armazem JJ"),
]
found = 0
for url, country, city, name in SITES:
    html = fetch(url)
    if not html:
        continue
    emails = [e for e in extract_emails(html) if not any(b in e.lower() for b in BLOCKED)]
    phones = extract_wa(html)
    if emails or phones:
        status = add_lead(name, (emails or [''])[0], (phones or [''])[0], '', country, city)
        if status != 'dup':
            found += 1
            print(f"  + {status} {name} | {emails[:1]} | {phones[:1]}", flush=True)
    time.sleep(2)
print(f"HUNT DONE: {found} new leads")
