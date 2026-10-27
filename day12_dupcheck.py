#!/usr/bin/env python3
"""Day-12 duplicate check: for a sample of wave recipients, count the Gmail
SENT threads in the last 24h. More than 1 = duplicate. Read-only.
"""
import sys, time, json
from urllib.parse import quote
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

csv_rows = [l.strip() for l in open('/home/ubuntu/day12_wave.txt') if l.strip()]
import csv as _csv
meta = {r['Lead ID']: r for r in _csv.DictReader(open('/home/ubuntu/leads.csv', newline='', encoding='utf-8'))}
sample = csv_rows[:4] + csv_rows[48:52] + csv_rows[-4:]

gm = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
if not gm:
    print('no gmail tab')
    sys.exit(1)
ws = connect(gm[0])
cdp = make_cdp(ws)
cdp('Page.enable')
cdp('Page.bringToFront')
time.sleep(1)

dups = 0
for lid in sample:
    em = (meta[lid]['Email'] or '').strip().lower()
    if not em:
        continue
    q = f'in:sent newer_than:1d to:{em}'
    cdp('Page.navigate', {'url': 'https://mail.google.com/mail/u/0/#search/' + quote(q)})
    time.sleep(5)
    v = js_eval(ws, """(() => {
      const main = document.querySelector('div[role="main"]');
      const txt = main ? (main.innerText||'') : '';
      const m = txt.match(/(\\d+)[\\u2013-](\\d+) of (\\d+)/);
      return JSON.stringify({count: m ? parseInt(m[3],10) : 0, head: txt.replace(/\\s+/g,' ').slice(0,90)});
    })()""", await_promise=False)
    try:
        d = json.loads(v)
    except Exception:
        d = {'count': -1, 'head': str(v)[:80]}
    flag = 'DUPLICATE!' if d.get('count', 0) > 1 else 'ok'
    if d.get('count', 0) > 1:
        dups += 1
    print(f"  {lid} {em[:38]:40s} sent_threads={d.get('count')} {flag}")
ws.close()
print('sample size:', len(sample), '| duplicates found:', dups)
