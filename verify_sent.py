#!/usr/bin/env python3
"""Verify an email actually landed in Gmail Sent (not just that compose closed).
Searches the Sent folder for the recipient address via the Gmail search box."""
import sys, time, json
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

email = sys.argv[1]
tabs = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
if not tabs:
    print("NO GMAIL TAB"); sys.exit(1)
tab = tabs[0]
ws = connect(tab)
cdp = make_cdp(ws)
cdp("Page.enable")
cdp("Page.bringToFront")
time.sleep(1)

# navigate to Sent
js_eval(ws, "(() => { location.hash = '#sent'; return 1; })()", await_promise=False)
time.sleep(4)

# open the search box and query
v = js_eval(ws, """(async () => {
  const box = document.querySelector('input[aria-label*="Search" i], input[placeholder*="Search" i]');
  if (!box) return 'no-search-box';
  box.focus();
  box.click();
  await new Promise(r => setTimeout(r, 300));
  return 'ok';
})()""")
print("search box:", v)
time.sleep(0.5)
cdp("Input.insertText", {"text": f"in:sent {email}"})
time.sleep(1)
cdp("Input.dispatchKeyEvent", {"type": "rawKeyDown", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13})
cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13})
time.sleep(5)

res = js_eval(ws, """(() => {
  const rows = Array.from(document.querySelectorAll('div[role="main"] div[role="listitem"], tr.zA, div.adn.ads'));
  const texts = rows.slice(0, 6).map(r => (r.innerText||'').replace(/\\s+/g,' ').slice(0,160));
  const body = document.body.innerText;
  const noMatch = /No emails matched|There are no emails/i.test(body);
  return JSON.stringify({count: rows.length, noMatch, rows: texts});
})()""", await_promise=False)
print("SENT SEARCH RESULT:", res)
ws.close()
