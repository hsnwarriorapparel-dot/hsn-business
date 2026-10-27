#!/usr/bin/env python3
"""Read FB buyer-intent group posts + go4WorldBusiness verification email."""
import sys, time, json
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

print('=== FB POSTS ===')
seen_urls = set()
for t in get_tabs():
    u = t.get('url','')
    if t['type'] == 'page' and 'facebook.com/groups' in u and u not in seen_urls:
        seen_urls.add(u)
        try:
            ws = connect(t)
            cdp = make_cdp(ws)
            cdp('Page.bringToFront')
            time.sleep(2)
            v = js_eval(ws, """(() => {
              const t = document.body ? document.body.innerText : '';
              return JSON.stringify(t.replace(/\\s+/g,' ').slice(0, 3000));
            })()""", await_promise=False)
            ws.close()
            print('--- URL:', u[:120])
            print('TITLE:', t.get('title','')[:80])
            print('TEXT:', str(v)[10:2600])
            print()
        except Exception as e:
            print('--- URL:', u[:120], 'ERR:', str(e)[:100])

print('=== GMAIL: go4worldbusiness verification result ===')
gm = [t for t in get_tabs() if 'mail.google' in t.get('url','') and t['type']=='page']
if gm:
    ws = connect(gm[0])
    cdp = make_cdp(ws)
    cdp('Page.navigate', {'url': 'https://mail.google.com/mail/u/0/#search/from%3Amarco%40go4worldbusiness.com'})
    time.sleep(8)
    js_eval(ws, """(() => { const r=document.querySelectorAll('tr')[0]; if(r) r.click(); return '1';})()""", await_promise=False)
    time.sleep(8)
    v = js_eval(ws, """(() => {
      const main = document.querySelector('div[role="main"]');
      return JSON.stringify(main ? (main.innerText||'').replace(/\\s+/g,' ').slice(0,2500) : 'nomain');
    })()""", await_promise=False)
    ws.close()
    print(str(v)[:2600])
