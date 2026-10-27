#!/usr/bin/env python3
"""Day-12 preflight (2026-10-26): verify Gmail / WhatsApp / IG session state.

- Opens a Gmail tab if none exists (PUT /json/new then Page.navigate) and
  checks that the account is logged in AND the Compose button is present.
- Probes the WhatsApp tab for the QR login screen vs a live #pane-side.
- Reports IG tab availability.
Read-only: no sends.
"""
import json, time, urllib.request, urllib.error, sys
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

CDP = 'http://127.0.0.1:9222'


def http_put(path):
    req = urllib.request.Request(CDP + path, method='PUT')
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read().decode()


def open_tab(url):
    try:
        http_put('/json/new?url=about:blank')
    except Exception as e:
        print('  /json/new PUT failed:', str(e)[:80])
    time.sleep(2)
    tabs = [t for t in get_tabs() if t['type'] == 'page']
    if not tabs:
        return None
    ws = connect(tabs[0])
    cdp = make_cdp(ws)
    cdp('Page.enable')
    cdp('Page.navigate', {'url': url})
    time.sleep(8)
    ws.close()
    return True


print('=== GMAIL ===')
gm = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
if not gm:
    print('  no gmail tab -> opening one')
    open_tab('https://mail.google.com/mail/u/0/#inbox')
    gm = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
if gm:
    ws = connect(gm[0])
    v = js_eval(ws, """(() => {
      const txt = document.body ? document.body.innerText : '';
      const btn = Array.from(document.querySelectorAll('div[role="button"], .T-I')).find(e => /^Compose$/i.test((e.innerText||'').trim()));
      return JSON.stringify({
        title: document.title,
        compose: !!btn,
        loggedIn: !/sign in|accounts.google.com/i.test(txt.slice(0,300)),
        head: txt.replace(/\\s+/g,' ').slice(0, 220)
      });
    })()""", await_promise=False)
    ws.close()
    print('  state:', v)
else:
    print('  GMAIL TAB UNAVAILABLE after open attempt')

print('=== WHATSAPP ===')
wa = [t for t in get_tabs() if 'web.whatsapp' in t['url'] and t['type'] == 'page']
print('  wa tabs:', len(wa))
for t in wa:
    for attempt in range(3):
        try:
            ws = connect(t)
            v = js_eval(ws, """(() => {
              const txt = document.body ? document.body.innerText : '';
              return JSON.stringify({
                qr: txt.includes('Scan to log in'),
                pane: !!document.querySelector('#pane-side'),
                title: document.title,
                head: txt.replace(/\\s+/g,' ').slice(0, 160)
              });
            })()""", await_promise=False)
            ws.close()
            print('  attempt', attempt + 1, '->', v)
            break
        except Exception as e:
            print('  attempt', attempt + 1, 'error:', str(e)[:70])
            time.sleep(4)

print('=== INSTAGRAM ===')
ig = [t for t in get_tabs() if 'instagram.com' in t['url'] and t['type'] == 'page']
print('  ig tabs:', len(ig))
for t in ig:
    print('   ', t['url'][:90])
