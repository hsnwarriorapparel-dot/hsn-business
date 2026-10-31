#!/usr/bin/env python3
"""Day 7 repair: rebuild malformed 18-col rows to the 15-col schema,
normalize all emails, dedupe by normalized email (keep first),
renumber duplicate Lead IDs, read back and verify."""
import csv, os, tempfile, re, html as ihtml

CSV = '/home/ubuntu/leads.csv'

def load():
    with open(CSV, newline='', encoding='utf-8-sig') as f:
        return list(csv.reader(f))

def clean_name(n):
    n = ihtml.unescape(n or '')
    n = re.sub(r'\s+', ' ', n).strip()
    low = n.lower()
    for pref in ['kontakt - ', 'kontakt | ', 'kontakt ', 'kontakt-', 'contact – ', 'contact - ',
                 'contact ', 'kontakt', 'home - ', 'www.', 'willkommen auf ']:
        if low.startswith(pref):
            n = n[len(pref):]
            low = n.lower()
    n = n.split(' | ')[0].strip()
    n = re.sub(r'\s*[-–—]\s*$', '', n).strip(' -|–')
    return n.strip() or 'Unknown Gym'

def norm_email(e):
    e = (e or '').strip()
    e = re.sub(r'^(%20|u00a0|\\u00a0|\s)+', '', e, flags=re.I)
    return e.lower().strip().strip('.,;')

def valid_email(e):
    if not e or e.count('@') != 1:
        return False
    dom = e.split('@')[1]
    if '.' not in dom:
        return False
    tld = dom.rsplit('.', 1)[1]
    if not re.fullmatch(r'[a-z]{2,}', tld):
        return False
    if re.search(r'\.(png|jpe?g|js|webp|svg|gif|css)$', e):
        return False
    if re.search(r'(sentry|wixpress|example|no-?reply|godaddy|wordpress|sitefactory|your?email|domain\.com|@2x|\.dewww)', e):
        return False
    return True

def clean_phone(p):
    p = (p or '').strip()
    if '*' in p:
        return ''
    p = re.sub(r'[^\d+]', '', p)
    digits = re.sub(r'\D', '', p)
    if len(digits) < 11:
        return ''
    return p if p.startswith('+') else '+' + digits

rows = load()
header = rows[0]
assert len(header) == 15, header
idx = {h: i for i, h in enumerate(header)}
iE, iS, iP = idx['Email'], idx['Status'], idx['Phone']

# ---- 1. rebuild malformed rows to 15-col schema
rebuilt = 0
out = [header]
for r in rows[1:]:
    if len(r) == 18:
        lid   = r[0]
        name  = clean_name(r[1])
        cntry = r[2]                       # was written into 'Type' slot
        city  = clean_name(r[3]) if r[3] and not r[3].isdigit() else ''
        email = norm_email(r[4])
        phone = clean_phone(r[5])
        ig    = (r[6] or '').lstrip('@').strip()
        note  = r[14] if len(r) > 14 else ''
        new = [''] * 15
        new[idx['Lead ID']] = lid
        new[idx['Name']] = name
        new[idx['Type']] = 'Gym/Club'
        new[idx['IG Username']] = ('@' + ig) if ig else ''
        new[idx['IG Profile Link']] = (f'https://www.instagram.com/{ig}/') if ig else ''
        new[idx['City']] = city if city and city.lower() != cntry.lower() else ''
        new[idx['Country']] = cntry
        new[iP] = phone
        new[idx['Phone Type']] = 'mobile' if phone else ''
        new[iE] = email if valid_email(email) else ''
        new[idx['Website']] = ''
        new[iS] = 'HUNTED (Day 6 pre-dawn, schema repaired Day 7)'
        new[idx['Profile Analysis']] = ''
        new[idx['Products Needed']] = 'Martial arts gear, uniforms'
        new[idx['Notes']] = note
        out.append(new)
        rebuilt += 1
    else:
        r = list(r) + [''] * (15 - len(r))
        r[iE] = norm_email(r[iE])
        if not valid_email(r[iE]):
            r[iE] = ''
        r[iP] = clean_phone(r[iP]) if r[iP] and 'WA' not in r[iS] else r[iP]
        out.append(r[:15])

# ---- 2. dedupe by normalized email (keep first)
seen = {}
dropped = []
final = [out[0]]
for r in out[1:]:
    e = r[iE]
    if e:
        if e in seen:
            dropped.append((r[0], r[idx['Name']][:30], e))
            continue
        seen[e] = r[0]
    final.append(r)

# ---- 3. renumber duplicate Lead IDs (first occurrence keeps the ID)
used = set()
renumbered = []
maxid = 0
for r in final[1:]:
    try:
        maxid = max(maxid, int(r[0][1:]))
    except ValueError:
        pass
nid = maxid + 1
for r in final[1:]:
    if r[0] in used:
        old = r[0]
        r = r[:]  # copy before mutate
        r[0] = f'L{nid:03d}'
        nid += 1
        renumbered.append((old, r[0], r[idx['Name']][:30]))
    used.add(r[0])
    final_rows = r

# rebuild final list with renumber applied
result = [header]
used = set()
nid = maxid + 1
for r in final[1:]:
    if r[0] in used:
        r = r[:]
        r[0] = f'L{nid:03d}'
        nid += 1
    used.add(r[0])
    result.append(r)

# ---- 4. atomic write
fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
    csv.writer(f).writerows(result)
os.replace(tmp, CSV)

# ---- 5. read back and verify
chk = load()
assert len(chk[0]) == 15
bad = [r[0] for r in chk[1:] if len(r) != 15]
ids = [r[0] for r in chk[1:]]
dup_ids = [i for i in set(ids) if ids.count(i) > 1]
emails = [r[iE].lower() for r in chk[1:] if r[iE]]
dup_emails = [e for e in set(emails) if emails.count(e) > 1]

print(f"Rebuilt 18->15 col rows : {rebuilt}")
print(f"Dropped email-dupes     : {len(dropped)}")
for d in dropped:
    print("   -", d)
print(f"Renumbered dup IDs      : {renumbered}")
print(f"Rows now                : {len(chk)-1} (was {len(rows)-1})")
print(f"READBACK: bad-col rows={len(bad)} dup-ids={len(dup_ids)} dup-emails={len(dup_emails)}")
print(f"Last ID                 : {chk[-1][0]}")

# ---- 6. ammo / candidate counts with the pipeline's own filter
ammo = wa_c = ig_c = 0
for r in chk[1:]:
    st = (r[iS] or '').lower()
    if r[iE] and 'email sent' not in st and 'failed' not in st:
        ammo += 1
    if (r[iP] or '').strip() and len(re.sub(r'\D', '', r[iP])) >= 11 and 'wa' not in st:
        wa_c += 1
    if (r[idx['IG Username']] or '').strip() and 'ig' not in st:
        ig_c += 1
print(f"AMMO after repair       : {ammo}")
print(f"WA candidates           : {wa_c}")
print(f"IG candidates           : {ig_c}")
