#!/usr/bin/env python3
"""Remove the UTF-8 BOM from leads.csv and make every reader BOM-safe.

Root cause: gmaps_daily_scrape.py read leads.csv with the default utf-8
encoding (so the BOM became part of the first header cell '\ufeffLead ID')
and then re-wrote that header back out, re-encoding the BOM as bytes.
Every DictReader script then failed with KeyError: 'Lead ID'.
"""
import csv, os, re, glob

LEADS = '/home/ubuntu/leads.csv'

# --- 1. strip the BOM from leads.csv (byte level, no CSV re-serialization) ---
with open(LEADS, 'rb') as f:
    raw = f.read()
if raw.startswith(b'\xef\xbb\xbf'):
    with open(LEADS, 'wb') as f:
        f.write(raw[3:])
    print('BOM stripped from leads.csv')
else:
    print('leads.csv has no BOM')

# --- 2. patch the writer so it can never re-add the BOM ---
ws = '/home/ubuntu/gmaps_daily_scrape.py'
s = open(ws, encoding='utf-8').read()
before = s
s = s.replace("    with open(LEADS) as f:\n        rows = list(csv.reader(f))",
              "    with open(LEADS, encoding='utf-8-sig', newline='') as f:\n        rows = list(csv.reader(f))")
s = s.replace("        with open(LEADS) as f:",
              "        with open(LEADS, encoding='utf-8-sig', newline='') as f:")
s = s.replace("    with os.fdopen(fd, 'w', newline='') as f:\n        csv.writer(f).writerows(rows)",
              "    with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:\n        csv.writer(f).writerows(rows)")
if s != before:
    open(ws, 'w', encoding='utf-8').write(s)
    print('patched writer:', ws)
else:
    print('writer patch: NO CHANGE (check manually)')

# --- 3. make every csv reader BOM-safe ---
targets = []
for pat in ('/home/ubuntu/day*.py', '/home/ubuntu/rebuild_tracker_day.py',
            '/home/ubuntu/make_wa_excel.py', '/home/ubuntu/hsn_counters.py',
            '/home/ubuntu/clean_contaminated_emails.py', '/home/ubuntu/safe_csv_update.py',
            '/home/ubuntu/ig_email_extractor.py', '/home/ubuntu/day*_*.py'):
    targets.extend(glob.glob(pat))
targets = sorted(set(targets))

patched = 0
for path in targets:
    try:
        s = open(path, encoding='utf-8').read()
    except Exception:
        continue
    orig = s
    # DictReader on the leads file -> utf-8-sig
    s = re.sub(r"open\((CSV|LEADS|'leads\.csv'|\"leads\.csv\"),\s*newline='',\s*encoding='utf-8'\)",
               lambda m: m.group(0).replace("encoding='utf-8'", "encoding='utf-8-sig'"), s)
    s = re.sub(r"open\((CSV|LEADS|'leads\.csv'|\"leads\.csv\"),\s*encoding='utf-8',\s*errors='replace'\)",
               lambda m: m.group(0).replace("encoding='utf-8'", "encoding='utf-8-sig'"), s)
    s = re.sub(r"open\((CSV|LEADS|'leads\.csv'|\"leads\.csv\"),\s*encoding='utf-8'\)",
               lambda m: m.group(0).replace("encoding='utf-8'", "encoding='utf-8-sig'"), s)
    # csv.reader with utf-8 (no errors=) -> utf-8-sig
    s = re.sub(r"csv\.(reader|DictReader)\(open\((CSV|LEADS),[^)]*encoding='utf-8'\)",
               lambda m: m.group(0).replace("encoding='utf-8'", "encoding='utf-8-sig'"), s)
    if s != orig:
        open(path, 'w', encoding='utf-8').write(s)
        patched += 1
        print('  patched reader:', os.path.basename(path))

print('readers patched:', patched)

# --- 4. verify ---
rows = list(csv.DictReader(open(LEADS, newline='', encoding='utf-8-sig')))
print('VERIFY rows:', len(rows), '| first fieldname:', list(rows[0].keys())[0])
print('VERIFY last Lead ID:', rows[-1]['Lead ID'])
