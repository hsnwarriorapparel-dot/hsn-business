#!/usr/bin/env python3
"""Day-12 independent verification: confirm the wave emails are really in the
Gmail SENT folder (not just marked in the CSV). Read-only.
"""
import sys, time, json, re
from urllib.parse import quote
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

QS = [
    'in:sent newer_than:1d subject:"HSN Warrior Apparels"',
    'in:sent newer_than:1d subject:"custom club apparel"',
    'in:sent newer_than:1d subject:"club gear manufacturing"',
    'in:sent newer_than:1d subject:"Branded uniforms"',
]

gm = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
if not gm:
    print('no gmail tab')
    sys.exit(1)
ws = connect(gm[0])
cdp = make_cdp(ws)
cdp('Page.enable')
cdp('Page.bringToFront')
time.sleep(1)
total = 0
for q in QS:
    cdp('Page.navigate', {'url': 'https://mail.google.com/mail/u/0/#search/' + quote(q)})
    time.sleep(6)
    v = js_eval(ws, """(() => {
      const rows = Array.from(document.querySelectorAll('div[role="listitem"], div.adn.ads'));
      const uniq = new Set();
      for (const r of rows) {
        const s = r.querySelector('span[email]');
        if (s) uniq.add(s.getAttribute('email'));
      }
      const main = document.querySelector('div[role="main"]');
      const head = main ? (main.innerText||'').replace(/\\s+/g,' ') : '';
      return JSON.stringify({count: uniq.size, head: head.slice(0,140),
        sample: Array.from(uniq).slice(0,6)});
    })()""", await_promise=False)
    try:
        d = json.loads(v)
    except Exception:
        print('  parse fail', str(v)[:120])
        continue
    total += d.get('count', 0)
    print(f"  [{q[12:52]}] -> {d.get('count')} sent threads | {d.get('head','')[:80]}")
    print('     sample:', d.get('sample'))
ws.close()
print('TOTAL distinct sent threads matched by subject variants:', total)
