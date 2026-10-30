#!/usr/bin/env python3
"""WA tab diagnosis with LONG timeout (90s). Never reloads the tab."""
import json, sys, urllib.request, time
import websocket

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9222/json/list', timeout=10))
wa = [t for t in tabs if 'web.whatsapp.com' in t.get('url', '') and t.get('type') == 'page']
print('WA tabs:', len(wa))
if not wa:
    print('NO_WA_TAB'); sys.exit(2)

t = wa[0]
print('tab id', t.get('id'), 'title', t.get('title'))
try:
    ws = websocket.create_connection(t['webSocketDebuggerUrl'], timeout=90,
                                    suppress_origin=True)
except Exception as e:
    print('WS CONNECT FAIL:', type(e).__name__, str(e)[:120]); sys.exit(3)

def cdp(method, params=None, _id=[1]):
    _id[0] += 1
    mid = _id[0]
    ws.send(json.dumps({'id': mid, 'method': method, 'params': params or {}}))
    deadline = time.time() + 90
    while time.time() < deadline:
        try:
            m = json.loads(ws.recv())
        except Exception as e:
            raise RuntimeError('recv:' + type(e).__name__)
        if m.get('id') == mid:
            return m
    raise RuntimeError('timeout')

t0 = time.time()
try:
    r = cdp('Runtime.evaluate', {'expression': """(() => {
      const body = (document.body && document.body.innerText) || '';
      const pane = !!document.querySelector('#pane-side');
      const qr = /Scan to log in|Log in to WhatsApp/i.test(body);
      return JSON.stringify({pane: pane, qr: qr, len: body.length, head: body.slice(0,300)});
    })()""", 'returnByValue': True})
    print('EVAL ok in %.1fs:' % (time.time() - t0),
          r.get('result', {}).get('result', {}).get('value'))
except Exception as e:
    print('EVAL FAIL after %.1fs:' % (time.time() - t0), type(e).__name__, str(e)[:120])
    sys.exit(4)
finally:
    try:
        ws.close()
    except Exception:
        pass
