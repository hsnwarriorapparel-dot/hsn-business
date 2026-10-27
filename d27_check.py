#!/usr/bin/env python3
"""Day-13 (2026-10-27) briefing checks: IG login, ufa-ms.de email, go4WorldBusiness, FB buyer posts."""
import sys, time, json, re
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

def tab_for(pred):
    for t in get_tabs():
        if t['type'] == 'page' and pred(t.get('url','')):
            return t
    return None

print('=== IG LOGIN CHECK ===')
ig = tab_for(lambda u: 'instagram.com' in u)
if ig:
    ws = connect(ig)
    v = js_eval(ws, """(() => {
      const t = document.body ? document.body.innerText : '';
      return JSON.stringify({login: /Log in|Log in to Instagram/i.test(t),
        loginUrl: location.href.includes('/accounts/login'),
        head: t.replace(/\\s+/g,' ').slice(0,220)});
    })()""", await_promise=False)
    ws.close()
    print(' ', str(v)[:400])

print('=== GMAIL: ufa-ms.de thread ===')
gm = tab_for(lambda u: 'mail.google' in u)
if gm:
    ws = connect(gm)
    cdp = make_cdp(ws)
    q = "from:ufa-ms.de"
    cdp('Page.navigate', {'url': 'https://mail.google.com/mail/u/0/#search/from%3Aufa-ms.de'})
    time.sleep(7)
    v = js_eval(ws, """(() => {
      const rows = Array.from(document.querySelectorAll('tr')).slice(0,5);
      return JSON.stringify(rows.map(r => (r.innerText||'').replace(/\\s+/g,' ').slice(0,400)));
    })()""", await_promise=False)
    print('  rows:', str(v)[:900])
    # open the thread
    v2 = js_eval(ws, """(() => {
      const r = document.querySelectorAll('tr')[0];
      if (!r) return JSON.stringify({err:'no row'});
      r.click();
      return JSON.stringify({clicked:true});
    })()""", await_promise=False)
    time.sleep(7)
    v3 = js_eval(ws, """(() => {
      const t = document.body ? document.body.innerText : '';
      const main = document.querySelector('div[role="main"]');
      return JSON.stringify({main: main ? (main.innerText||'').replace(/\\s+/g,' ').slice(0,2500) : t.slice(0,2000)});
    })()""", await_promise=False)
    print('  thread:', str(v3)[:2600])
    ws.close()

print('=== go4WorldBusiness verification ===')
g4 = tab_for(lambda u: 'go4worldbusiness' in u.lower())
if g4:
    ws = connect(g4)
    v = js_eval(ws, """(() => {
      const t = document.body ? document.body.innerText : '';
      return JSON.stringify({url: location.href, head: t.replace(/\\s+/g,' ').slice(0,900)});
    })()""", await_promise=False)
    ws.close()
    print(' ', str(v)[:1200])

print('=== FB buyer-intent posts ===')
for t in get_tabs():
    if t['type'] == 'page' and 'facebook.com/groups' in t.get('url',''):
        print(' URL:', t['url'][:110], '| title:', t.get('title','')[:70])
