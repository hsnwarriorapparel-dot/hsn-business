#!/usr/bin/env python3
"""Capture the WhatsApp Web login QR code for the user to scan.

The WA session has been QR-dead since 2026-10-24. The user re-links from the
phone; this script just saves a fresh, readable PNG of the QR canvas so it can
be delivered to Telegram. NEVER reload the WA tab (a duplicate tab kills the
pane and the QR misreads as a dead session).
"""
import base64
import json
import os
import sys
import time

sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval, make_cdp

OUT = '/home/ubuntu/wa_qr_day17.png'

tabs = [t for t in get_tabs() if 'web.whatsapp.com' in t['url'] and t['type'] == 'page']
print('WA tabs:', len(tabs))
if not tabs:
    print('NO_WA_TAB')
    sys.exit(2)

ws = connect(tabs[0])
cdp = make_cdp(ws)
cdp('Page.bringToFront')
time.sleep(2)

state = json.loads(js_eval(ws, """(() => {
  const body = (document.body && document.body.innerText) || '';
  const pane = !!document.querySelector('#pane-side');
  const qr = /Scan to log in|Log in to WhatsApp/i.test(body);
  const canvases = Array.from(document.querySelectorAll('canvas'));
  const qrCanvas = canvases.find(c => { const r = c.getBoundingClientRect();
                                        return r.width > 120 && r.height > 120; });
  let rect = null;
  if (qrCanvas) {
    const r = qrCanvas.getBoundingClientRect();
    rect = {x: Math.round(r.x), y: Math.round(r.y),
            w: Math.round(r.width), h: Math.round(r.height)};
  }
  return JSON.stringify({pane: pane, qr: qr, nCanvas: canvases.length, rect: rect,
                          head: body.slice(0, 120).replace(/\\n/g, ' | ')});
})()""", await_promise=False) or '{}')
print('state:', state)

if not state.get('qr'):
    print('QR_NOT_SHOWN - session may be alive instead')
    ws.close()
    sys.exit(3)

rect = state.get('rect')
if rect:
    shot = cdp('Page.captureScreenshot', {
        'format': 'png',
        'clip': {'x': max(0, rect['x'] - 12), 'y': max(0, rect['y'] - 12),
                 'width': rect['w'] + 24, 'height': rect['h'] + 24, 'scale': 2},
    })
    data = shot.get('data')
    if data:
        with open(OUT, 'wb') as f:
            f.write(base64.b64decode(data))
        print('QR saved:', OUT, os.path.getsize(OUT), 'bytes')
        ws.close()
        sys.exit(0)

# fallback: full viewport
shot = cdp('Page.captureScreenshot', {'format': 'png'})
if shot.get('data'):
    with open(OUT, 'wb') as f:
        f.write(base64.b64decode(shot['data']))
    print('QR (full viewport) saved:', OUT, os.path.getsize(OUT), 'bytes')
    ws.close()
    sys.exit(0)

print('CAPTURE_FAILED')
ws.close()
sys.exit(4)
