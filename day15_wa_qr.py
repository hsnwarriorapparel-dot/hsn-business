#!/usr/bin/env python3
"""Check WhatsApp Web session state (QR vs live pane). Never reload a WA tab."""
import sys
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval

tabs = [t for t in get_tabs() if 'web.whatsapp.com' in t.get('url', '') and t.get('type') == 'page']
print('WA tabs found:', len(tabs))
for t in tabs:
    try:
        ws = connect(t)
        v = js_eval(ws, """(() => {
          const body = (document.body.innerText || '');
          const pane = !!document.querySelector('#pane-side');
          const qr = /Scan to log in|Log in to WhatsApp/i.test(body);
          return JSON.stringify({pane, qr, head: body.slice(0,140)});
        })()""", await_promise=False)
        ws.close()
        print('  tab', t.get('id'), '->', v)
    except Exception as e:
        print('  tab', t.get('id'), '-> ERR', str(e)[:80])
