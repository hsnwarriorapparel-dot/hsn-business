#!/usr/bin/env python3
"""Day-22 (2026-11-05) pre-flight: Gmail ground truth + WA session state.

Read-only. Establishes:
  1. how many emails were already sent today (daily quota headroom)
  2. how many conversations exist in the Sent folder (baseline for the audit)
  3. whether WhatsApp Web is alive (#pane-side) or showing the login QR
"""
import json
import re
import sys
import time
import urllib.parse

sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

# Compute the dates - a hardcoded literal goes stale every day and reports
# the WRONG ground truth (it reported 2026-11-05 sends on 2026-11-07).
import datetime as _dt
_today = _dt.datetime.now(_dt.timezone.utc).date()
TODAY = _today.strftime('%Y/%m/%d')
YESTERDAY = (_today - _dt.timedelta(days=1)).strftime('%Y/%m/%d')


def main():
    tabs = get_tabs()
    gm = [t for t in tabs if 'mail.google' in t.get('url', '') and t.get('type') == 'page']
    if not gm:
        print('NO GMAIL TAB')
    else:
        ws = connect(gm[0])
        cdp = make_cdp(ws)
        cdp('Page.enable')
        cdp('Page.bringToFront')
        time.sleep(1)

        def cnt(q, wait=5):
            cdp('Page.navigate', {'url': 'https://mail.google.com/mail/u/0/#search/' + urllib.parse.quote(q)})
            time.sleep(wait)
            v = js_eval(ws, """(()=>{const m=document.querySelector('div[role="main"]');
                const t=m?m.innerText:'';
                const x=t.match(/([\\d,]+)\\s*[–-]\\s*[\\d,]+\\s+of\\s+([\\d,]+)\\s+Conversations/);
                const y=t.match(/([\\d,]+)\\s+Conversations/);
                return JSON.stringify({c:x?x[2]:(y?y[1]:null), head:t.slice(0,400)});})()""",
                           await_promise=False)
            try:
                return json.loads(v or '{}')
            except Exception:
                return {'c': None, 'raw': str(v)[:200]}

        print('--- GMAIL GROUND TRUTH ---')
        r = cnt('in:sent after:' + TODAY, wait=6)
        print('  in:sent after:%s -> %s' % (TODAY, r.get('c')))
        r0 = cnt('in:sent after:' + YESTERDAY, wait=6)
        print('  in:sent after:%s -> %s' % (YESTERDAY, r0.get('c')))
        r2 = cnt('in:sent newer_than:2d', wait=6)
        print('  in:sent newer_than:2d -> %s' % r2.get('c'))
        r3 = cnt('in:sent newer_than:30d', wait=6)
        print('  in:sent newer_than:30d -> %s' % r3.get('c'))
        # drafts that may indicate failed sends
        r4 = cnt('in:drafts newer_than:1d', wait=6)
        print('  in:drafts newer_than:1d -> %s' % r4.get('c'))
        ws.close()

    print('--- WHATSAPP STATE ---')
    wa = [t for t in tabs if 'web.whatsapp.com' in t.get('url', '') and t.get('type') == 'page']
    print('  WA tabs:', len(wa))
    for i, t in enumerate(wa):
        try:
            ws = connect(t)
            cdp = make_cdp(ws)
            cdp('Page.bringToFront')
            time.sleep(2)
            st = json.loads(js_eval(ws, """(() => {
                const body = (document.body && document.body.innerText) || '';
                const pane = !!document.querySelector('#pane-side');
                const qr = /Scan to log in|Log in to WhatsApp|Link your phone/i.test(body);
                return JSON.stringify({pane: pane, qr: qr, head: body.slice(0,140).replace(/\\n/g,' | ')});
            })()""", await_promise=False) or '{}')
            print('  tab%d: %s' % (i, st))
            ws.close()
        except Exception as e:
            print('  tab%d probe error: %s' % (i, str(e)[:100]))


if __name__ == '__main__':
    main()
