#!/usr/bin/env python3
"""Capture the WhatsApp Web QR code as a PNG so the user can re-link from phone/VNC.
Reads the <img> element of the QR screen (no page reload - WA allows one tab)."""
import sys, base64, json, time, urllib.request
import websocket

CDP = 'http://127.0.0.1:9222'
OUT = '/home/ubuntu/wa_qr_day13.png'

tabs = json.load(urllib.request.urlopen(CDP + '/json/list'))
wa = [t for t in tabs if 'web.whatsapp' in t.get('url', '') and t.get('type') == 'page']
if not wa:
    print('NO WA TAB')
    sys.exit(1)
t = wa[0]
ws = websocket.create_connection(t['webSocketDebuggerUrl'], timeout=30, suppress_origin=True)
_id = [0]


def cdp(method, params=None):
    _id[0] += 1
    ws.send(json.dumps({'id': _id[0], 'method': method, 'params': params or {}}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get('id') == _id[0]:
            if 'error' in msg:
                raise RuntimeError(str(msg['error']))
            return msg.get('result', {})


try:
    cdp('Page.enable')
    time.sleep(1)
    res = cdp('Runtime.evaluate', {
        'expression': """(() => {
            const imgs = Array.from(document.querySelectorAll('img, canvas'));
            for (const el of imgs) {
                const r = el.getBoundingClientRect();
                if (r.width > 150 && r.width < 400 && r.height > 150 && r.height < 400) {
                    if (el.tagName === 'IMG' && el.src.startsWith('data:image')) {
                        return el.src;
                    }
                }
            }
            return '';
        })()""", 'returnByValue': True})
    data = res.get('result', {}).get('value', '')
    if not data:
        # fallback: full-page screenshot of the QR screen
        shot = cdp('Page.captureScreenshot', {'format': 'png', 'fromSurface': True})
        data = shot.get('data', '')
        if data:
            open(OUT, 'wb').write(base64.b64decode(data))
            print('saved full screenshot ->', OUT)
            sys.exit(0)
    else:
        b64 = data.split(',', 1)[1]
        open(OUT, 'wb').write(base64.b64decode(b64))
        print('saved QR image ->', OUT)
except Exception as e:
    print('ERR', type(e).__name__, str(e)[:120])
    sys.exit(1)
finally:
    ws.close()
