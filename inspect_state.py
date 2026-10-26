import csv, re, os, datetime
from collections import Counter

path = "/home/ubuntu/leads.csv"
rows = list(csv.DictReader(open(path, newline='', encoding='utf-8-sig')))
print("total rows:", len(rows))

def st(r): return (r.get('Status') or '').lower()
def em(r): return (r.get('Email') or '').strip()

ammo = [r for r in rows if em(r) and 'email sent' not in st(r) and 'failed' not in st(r) and 'excluded' not in st(r)]
print("AMMO:", len(ammo))
print("email sent:", sum(1 for r in rows if 'email sent' in st(r)))
print("failed(any):", sum(1 for r in rows if 'failed' in st(r)))
print("excluded:", sum(1 for r in rows if 'excluded' in st(r)))
print("ig done:", sum(1 for r in rows if 'ig followed' in st(r) or 'ig dm' in st(r)))
print("wa sent:", sum(1 for r in rows if 'whatsapp sent' in st(r) or 'wa sent' in st(r)))
print("phone present:", sum(1 for r in rows if (r.get('Phone') or '').strip()))

ids = []
for r in rows:
    m = re.match(r'L(\d+)$', (r.get('Lead ID') or '').strip())
    if m:
        ids.append(int(m.group(1)))
print("max L id:", max(ids) if ids else None)

for r in ammo[:15]:
    print("AMMO:", r.get('Lead ID'), "|", (r.get('Name') or '')[:32], "|", em(r), "|", r.get('Country'), "|", (r.get('Status') or '')[:45])

c = Counter()
for r in rows:
    s = (r.get('Status') or '')
    for m in re.finditer(r'(Day[- ]?\d+[^|;,)]*)', s):
        c[m.group(1).strip()] += 1
print("--- day tags ---")
for k, v in sorted(c.items(), key=lambda x: -x[1])[:20]:
    print("  ", k, v)

c2 = Counter()
for r in rows:
    s = (r.get('Status') or '')
    for m in re.finditer(r'HUNTED \(([^)]*)\)', s):
        c2[m.group(1)] += 1
print("--- hunted tags ---")
for k, v in sorted(c2.items(), key=lambda x: -x[1])[:20]:
    print("  ", k, v)

for f in ["/home/ubuntu/day6_log.txt", "/home/ubuntu/leads.csv", "/home/ubuntu/HWA_Lead_Tracker.xlsx", "/home/ubuntu/gmaps_scrape_log.txt"]:
    if os.path.exists(f):
        print("MTIME", f, datetime.datetime.utcfromtimestamp(os.path.getmtime(f)))
    else:
        print("MISSING", f)
print("NOW", datetime.datetime.utcnow())
