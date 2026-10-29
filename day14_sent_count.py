#!/usr/bin/env python3
"""Independent Gmail sent-count audit across all 4 subject variants."""
import sys, json, time, urllib.parse
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

tabs = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
ws = connect(tabs[0])
cdp = make_cdp(ws)
cdp('Page.enable')
cdp('Page.bringToFront')
time.sleep(1)


def cnt(q):
    cdp('Page.navigate', {'url': 'https://mail.google.com/mail/u/0/#search/' + urllib.parse.quote(q)})
    time.sleep(4.5)
    v = js_eval(ws, """(()=>{const m=document.querySelector('div[role="main"]');const t=m?m.innerText:'';const x=t.match(/(\\d+)\\s*[–-]\\s*\\d+\\s+of\\s+(\\d+)/);return JSON.stringify({c:x?x[2]:null});})()""",
                   await_promise=False)
    c = json.loads(v or '{}').get('c')
    try:
        return int(c)
    except Exception:
        return 0


VARIANTS = [
    'Custom martial arts gear for',
    'HSN Warrior Apparels - club gear manufacturing for',
    'Branded uniforms & equipment for',
    'x HSN Warrior Apparels - custom club apparel',
]
tot = 0
for sv in VARIANTS:
    c = cnt('in:sent newer_than:1d subject:"' + sv + '"')
    print(f'  "{sv}" -> {c}')
    tot += c
print('TOTAL SENT (4 subject variants, newer_than:1d):', tot)
ws.close()
