#!/usr/bin/env python3
"""Check Gmail Sent for leads whose CSV status marker may have been clobbered
by a concurrent full-file CSV writer. For each such lead, query
`in:sent newer_than:1d to:<email>` -- 1 = it was really sent (safe to
re-mark), 0 = it was NOT sent (must be sent), >1 = DUPLICATE (report)."""
import sys, json, time, csv, re, urllib.parse
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

CSV = '/home/ubuntu/leads.csv'
WAVE = '/home/ubuntu/day13_wave.txt'

tabs = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
if not tabs:
    print('NO GMAIL TAB')
    sys.exit(1)
ws = connect(tabs[0])
cdp = make_cdp(ws)


def search(q):
    url = 'https://mail.google.com/mail/u/0/#search/' + urllib.parse.quote(q)
    cdp('Page.navigate', {'url': url})
    time.sleep(4.5)
    v = js_eval(ws, """(() => {
        const main = document.querySelector('div[role="main"]');
        const txt = main ? main.innerText : '';
        const m = txt.match(/(\\d+)\\s*[–-]\\s*\\d+\\s+of\\s+(\\d+)/);
        return JSON.stringify({count: m ? m[2] : null});
    })()""", await_promise=False)
    return int(json.loads(v or '{}').get('count') or 0)


rows = list(csv.DictReader(open(CSV, newline='', encoding='utf-8-sig')))
d = {r['Lead ID']: r for r in rows}
wave = [l.strip() for l in open(WAVE) if l.strip()]
suspects = []
for lid in wave:
    r = d.get(lid)
    if not r:
        continue
    st = (r.get('Status') or '')
    if 'email sent' not in st.lower():
        suspects.append((lid, (r.get('Name') or '')[:28], (r.get('Email') or '').strip().lower()))

print('suspect leads (CSV marker missing):', len(suspects))
results = {}
for lid, name, email in suspects:
    n = search('in:sent newer_than:1d to:' + email)
    results[lid] = n
    verdict = 'SENT (re-mark)' if n == 1 else ('NOT SENT' if n == 0 else 'DUPLICATE!')
    print(f"  {verdict:16} {lid} {name:30} {email[:40]} -> {n}")
    time.sleep(1)

json.dump(results, open('/home/ubuntu/day13_marker_audit.json', 'w'), indent=1)
print('written /home/ubuntu/day13_marker_audit.json')
ws.close()
