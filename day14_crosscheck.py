#!/usr/bin/env python3
"""Cross-check: today's recipients must not overlap with Day-13's recipients,
and every one of today's recipients must have exactly ONE Gmail sent thread."""
import csv, re, sys, json, time, urllib.parse
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

rows = list(csv.DictReader(open('/home/ubuntu/leads.csv', newline='', encoding='utf-8')))
d13, d14 = [], []
for r in rows:
    st = (r.get('Status') or '')
    e = (r.get('Email') or '').strip().lower()
    if not e:
        continue
    if 'email sent (Daily 2026-10-28)' in st:
        d14.append((r['Lead ID'], e, r.get('Name', '')))
    elif 'email sent (Daily 2026-10-27)' in st:
        d13.append((r['Lead ID'], e, r.get('Name', '')))

print('Day-14 recipients:', len(d14))
print('Day-13 recipients:', len(d13))
e13 = set(e for _, e, _ in d13)
overlap = [(lid, e, n) for lid, e, n in d14 if e in e13]
print('OVERLAP Day13 vs Day14:', overlap if overlap else 'NONE')
e14 = Counter = {}
seen = {}
for lid, e, n in d14:
    seen.setdefault(e, []).append(lid)
dups = {k: v for k, v in seen.items() if len(v) > 1}
print('duplicate recipients inside Day-14:', dups if dups else 'NONE')

# per-recipient Gmail thread count for today's set
tabs = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
ws = connect(tabs[0])
cdp = make_cdp(ws)
cdp('Page.enable')
cdp('Page.bringToFront')
time.sleep(1)


def cnt(q):
    cdp('Page.navigate', {'url': 'https://mail.google.com/mail/u/0/#search/' + urllib.parse.quote(q)})
    time.sleep(4.0)
    v = js_eval(ws, """(()=>{const m=document.querySelector('div[role="main"]');const t=m?m.innerText:'';const x=t.match(/(\\d+)\\s*[–-]\\s*\\d+\\s+of\\s+(\\d+)/);return JSON.stringify({c:x?x[2]:null});})()""",
                   await_promise=False)
    try:
        return int(json.loads(v or '{}').get('c'))
    except Exception:
        return 0


print()
print('=== per-recipient thread count (today) ===')
one = multi = zero = 0
multi_list = []
zero_list = []
for lid, e, n in d14:
    c = cnt('in:sent newer_than:2d to:' + e)
    if c == 1:
        one += 1
    elif c == 0:
        zero += 1
        zero_list.append((lid, e, n))
    else:
        multi += 1
        multi_list.append((lid, e, n, c))
print('exactly 1:', one, '| 0:', zero, '| >1:', multi)
for z in zero_list:
    print('   ZERO', z)
for m in multi_list:
    print('   MULTI', m)
ws.close()
