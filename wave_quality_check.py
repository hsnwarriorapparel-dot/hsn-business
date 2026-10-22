#!/usr/bin/env python3
"""List tonight's 100-wave rows; flag name-vs-email-domain mismatches (scrape artifacts)."""
import csv, re
rows = list(csv.reader(open('/home/ubuntu/leads.csv', encoding='utf-8', errors='replace')))
idx = {h: i for i, h in enumerate(rows[0])}

def valid_email(e):
    e = re.sub(r'^(%20|u00a0|\s)+', '', (e or '').strip().lower())
    return bool(re.match(r'^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$', e)) and 'http' not in e

ACTIVE_ST = ['follow-up', 'hot lead', 'negotiat', 'sample quote', 'awaiting']
ammo = []
for r in rows[1:]:
    st = (r[idx['Status']] or '').lower()
    if not (r[idx['Email']] or '').strip(): continue
    if 'email sent' in st or 'failed' in st or 're-hunt' in st: continue
    if any(m in st for m in ACTIVE_ST): continue
    if not valid_email(r[idx['Email']]): continue
    ammo.append(r)
wave = ammo[:100]
print(f"wave size: {len(wave)}")
for r in wave:
    name, email, city, country, site = r[1], r[idx['Email']].strip(), r[idx['City']], r[idx['Country']], (r[idx['Website']] or '').strip()
    dom = email.split('@')[1] if '@' in email else '?'
    # name words vs email local part / domain similarity heuristic
    nl = re.sub(r'[^a-z0-9]', '', name.lower())
    dl = re.sub(r'[^a-z0-9]', '', dom)
    flag = ''
    if nl and dl and not any(chunk in dl for chunk in [nl[i:i+5] for i in range(max(1, len(nl)-4)) if len(nl)>=5]):
        flag = ' <-- MISMATCH?'
    if len(nl) < 6 or name.lower() in ('contactos', 'contact', 'contact us', 'kontakt', 'impressum'):
        flag = ' <-- ARTIFACT NAME'
    print(f"{r[0]} | {name[:34]:34} | {email[:38]:38} | {country or '?':12} | {site[:40]:40}{flag}")
