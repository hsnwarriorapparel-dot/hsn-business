#!/usr/bin/env python3
"""WA session check with a long timeout - never reload the tab."""
import json, sys, urllib.request
import websocket

WA_ID = 'E0CB9AA08F70F0265170BD5B6B704F2B'
try:
    tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9222/json/list', timeout=10))
except Exception as e:
    print('CDP list err', e); sys.exit(1)

wa = [t for t in tabs if 'web.whatsapp.com' in t.get('url', '')]
print('WA tabs:', len(wa))
if not wa:
    print('NO_WA_TAB'); sys.exit(2)

t = wa[0]
try:
    ws = websocket.create_connection(t['webSocketDebuggerUrl'], timeout=25,
                                    suppress_origin=True)
except Exception as e:
    print('WS CONNECT FAIL:', str(e)[:120]); sys.exit(3)

expr = """(() => {
  const body = (document.body && document.body.innerText) || '';
  const pane = !!document.querySelector('#pane-side');
  const qr = /Scan to log in|Log in to WhatsApp/i.test(body);
  return JSON.stringify({pane: pane, qr: qr, len: body.length, head: body.slice(0,200)});
})()"""
ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate',
                    'params': {'expression': expr, 'returnByValue': True}}))
try:
    while True:
        msg = json.loads(ws.recv())
        if msg.get('id') == 1:
            r = msg.get('result', {}).get('result', {}).get('value')
            print('RESULT:', r)
            break
except Exception as e:
    print('EVAL FAIL:', str(e)[:120]); sys.exit(4)
finally:
    try:
        ws.close()
    except Exception:
        pass
