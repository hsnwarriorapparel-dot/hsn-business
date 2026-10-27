#!/usr/bin/env python3
"""Extract the WhatsApp QR code image from the page DOM as a PNG file.

Read-only on the WA tab and does NOT bring it to the front (a focus switch
would break the concurrent Gmail wave, whose mouse clicks are viewport based).
"""
import base64, re, sys, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval

OUT = '/home/ubuntu/wa_qr_day12.png'

wa = [t for t in get_tabs() if 'web.whatsapp' in t['url'] and t['type'] == 'page']
if not wa:
    print('no WA tab')
    sys.exit(1)
ws = connect(wa[0])
v = js_eval(ws, """(() => {
  const imgs = Array.from(document.querySelectorAll('img'));
  const qr = imgs.find(i => /^data:image\\/(png|jpeg)/i.test(i.src||''));
  if (qr) return qr.src;
  const c = document.querySelector('canvas');
  if (c) { try { return c.toDataURL('image/png'); } catch(e) {} }
  return 'NONE';
})()""", await_promise=False)
ws.close()
if not v or v == 'NONE':
    print('no QR image found in DOM')
    sys.exit(2)
m = re.match(r'data:image/(\w+);base64,(.*)', v, re.S)
if not m:
    print('unexpected data format:', str(v)[:60])
    sys.exit(3)
ext, b64 = m.group(1), m.group(2)
data = base64.b64decode(b64)
with open(OUT, 'wb') as f:
    f.write(data)
print('QR written:', OUT, len(data), 'bytes, format', ext)
