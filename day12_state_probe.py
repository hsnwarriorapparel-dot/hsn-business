#!/usr/bin/env python3
"""Day-12: dismiss any Gmail beforeunload dialog ('Leave site?') and re-probe
WhatsApp + Gmail session state. Read-only apart from clicking Cancel.
"""
import json, time, sys
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

print('=== CANCEL GMAIL beforeunload dialog ===')
for t in [x for x in get_tabs() if x['type'] == 'page']:
    if 'mail.google' not in t['url']:
        continue
    try:
        ws = connect(t)
        v = js_eval(ws, """(() => {
          const btns = Array.from(document.querySelectorAll('div[role="button"], button'));
          const cancel = btns.find(b => /^Cancel$/i.test((b.innerText||'').trim()));
          if (cancel) { cancel.click(); return 'cancelled'; }
          return 'no-dialog';
        })()""", await_promise=False)
        ws.close()
        print('  gmail tab', t['id'][:8], '->', v)
    except Exception as e:
        print('  gmail tab error:', str(e)[:80])
    time.sleep(1)

print('=== GMAIL READY CHECK ===')
gm = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
print('  gmail tabs:', len(gm))
for t in gm:
    try:
        ws = connect(t)
        v = js_eval(ws, """(() => {
          const btn = Array.from(document.querySelectorAll('div[role="button"], .T-I')).find(e => /^Compose$/i.test((e.innerText||'').trim()));
          const txt = document.body ? document.body.innerText : '';
          return JSON.stringify({compose: !!btn, title: document.title,
            dialog: /Leave site\\?/i.test(txt),
            head: txt.replace(/\\s+/g,' ').slice(0,150)});
        })()""", await_promise=False)
        ws.close()
        print('  ->', v)
    except Exception as e:
        print('  error:', str(e)[:80])

print('=== WHATSAPP PROBE (per tab, 2 attempts) ===')
wa = [t for t in get_tabs() if 'web.whatsapp' in t['url'] and t['type'] == 'page']
print('  wa tabs:', len(wa))
for t in wa:
    for attempt in range(2):
        try:
            ws = connect(t)
            cdp = make_cdp(ws)
            cdp('Runtime.enable')
            v = js_eval(ws, """(() => {
              const txt = document.body ? document.body.innerText : '';
              return JSON.stringify({qr: /Scan to log in/i.test(txt),
                pane: !!document.querySelector('#pane-side'),
                title: document.title,
                head: txt.replace(/\\s+/g,' ').slice(0,200)});
            })()""", await_promise=False)
            ws.close()
            print('  attempt', attempt + 1, '->', v)
            break
        except Exception as e:
            print('  attempt', attempt + 1, 'error:', str(e)[:70])
            time.sleep(3)
