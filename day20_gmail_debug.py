#!/usr/bin/env python3
"""Day-20 debug: dump raw Gmail search-page text so the count can be parsed."""
import json
import sys
import time
import urllib.parse

sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

tabs = get_tabs()
gm = [t for t in tabs if 'mail.google' in t.get('url', '') and t.get('type') == 'page']
ws = connect(gm[0])
cdp = make_cdp(ws)
cdp('Page.enable')
cdp('Page.bringToFront')
time.sleep(1)

for q in ['in:sent after:2026/11/03', 'in:sent newer_than:2d', 'in:drafts newer_than:1d']:
    cdp('Page.navigate', {'url': 'https://mail.google.com/mail/u/0/#search/' + urllib.parse.quote(q)})
    time.sleep(7)
    v = js_eval(ws, """(()=>{
        const m=document.querySelector('div[role="main"]');
        const t=m?m.innerText:(document.body?document.body.innerText:'');
        return JSON.stringify({len:t.length, text:t.slice(0,1200)});})()""",
                   await_promise=False)
    print('=== QUERY:', q)
    try:
        d = json.loads(v or '{}')
        print('  len:', d.get('len'))
        print('  ---')
        print(d.get('text', '')[:1200])
        print('  ---')
    except Exception as e:
        print('  raw:', str(v)[:400])
ws.close()
