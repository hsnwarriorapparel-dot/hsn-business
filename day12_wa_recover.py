#!/usr/bin/env python3
"""Recover the WhatsApp Web tab: the CDP socket times out (page frozen or
throttled). Steps:
  1. close the frozen WA tab via /json/close/<id>
  2. open a fresh WA tab (PUT /json/new) and navigate it to web.whatsapp.com
  3. probe for the QR login screen vs a live chat pane
NOTE: WA Web allows only ONE active tab per profile - the old tab is closed
before the new one is opened (never two WA tabs at once).
"""
import json, time, urllib.request, sys
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

CDP = 'http://127.0.0.1:9222'


def close_tab(tab_id):
    try:
        urllib.request.urlopen(CDP + '/json/close/' + tab_id, timeout=10).read()
        return True
    except Exception as e:
        return 'err:' + str(e)[:60]


def new_tab():
    req = urllib.request.Request(CDP + '/json/new?url=about:blank', method='PUT')
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())


wa = [t for t in get_tabs() if 'web.whatsapp' in t['url'] and t['type'] == 'page']
print('existing WA tabs:', len(wa))
for t in wa:
    print('  closing', t['id'][:10], t['url'][:60], '->', close_tab(t['id']))
time.sleep(3)

try:
    nt = new_tab()
    print('new tab id:', nt.get('id', '')[:10])
except Exception as e:
    print('new tab failed:', str(e)[:100])
    sys.exit(1)

time.sleep(2)
tabs = [t for t in get_tabs() if t['type'] == 'page']
target = None
for t in tabs:
    if t.get('id', '').startswith(nt.get('id', '')[:8]):
        target = t
        break
if not target:
    target = tabs[0]
print('navigating', target['id'][:10])
ws = connect(target)
cdp = make_cdp(ws)
cdp('Page.enable')
cdp('Page.navigate', {'url': 'https://web.whatsapp.com/'})
time.sleep(12)
v = js_eval(ws, """(() => {
  const txt = document.body ? document.body.innerText : '';
  return JSON.stringify({qr: /Scan to log in/i.test(txt),
    pane: !!document.querySelector('#pane-side'),
    title: document.title,
    head: txt.replace(/\\s+/g,' ').slice(0,220)});
})()""", await_promise=False)
ws.close()
print('WA NEW TAB STATE:', v)
