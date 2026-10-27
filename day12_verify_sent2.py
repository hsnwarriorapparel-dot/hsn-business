#!/usr/bin/env python3
"""Day-12 independent verification v2: count the wave emails in Gmail SENT.

Gmail's sent rows do not expose span[email]; the reliable signal is the
"1-50 of N Conversations" header plus the visible recipient/subject text.
Read-only.
"""
import sys, time, json, re
from urllib.parse import quote
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

gm = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
if not gm:
    print('no gmail tab')
    sys.exit(1)
ws = connect(gm[0])
cdp = make_cdp(ws)
cdp('Page.enable')
cdp('Page.bringToFront')
time.sleep(1)


def probe(q):
    cdp('Page.navigate', {'url': 'https://mail.google.com/mail/u/0/#search/' + quote(q)})
    time.sleep(6)
    v = js_eval(ws, """(() => {
      const main = document.querySelector('div[role="main"]');
      const txt = main ? (main.innerText||'') : '';
      const m = txt.match(/(\\d+)[\\u2013-](\\d+) of (\\d+)/);
      const rows = Array.from(document.querySelectorAll('div[role="listitem"]'));
      const lines = rows.slice(0,6).map(r => (r.innerText||'').replace(/\\s+/g,' ').slice(0,110));
      return JSON.stringify({count: m ? parseInt(m[3],10) : 0, rows: rows.length, sample: lines,
        head: txt.replace(/\\s+/g,' ').slice(0,100)});
    })()""", await_promise=False)
    try:
        return json.loads(v)
    except Exception:
        return {'count': -1, 'sample': [], 'head': str(v)[:120]}


for q in ['in:sent newer_than:1d',
          'in:sent newer_than:1d subject:"custom club apparel"',
          'in:sent newer_than:1d subject:"Branded uniforms & equipment"',
          'in:sent newer_than:1d subject:"club gear manufacturing"',
          'in:sent newer_than:1d subject:"Custom martial arts gear"']:
    d = probe(q)
    print(f"[{q}] -> conversations={d.get('count')} rows={d.get('rows')}")
    print('   head:', d.get('head', '')[:90])
    for s in d.get('sample', [])[:3]:
        print('     ', s)
ws.close()
