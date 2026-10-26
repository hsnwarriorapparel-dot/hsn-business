#!/usr/bin/env python3
"""Verify an email landed in Gmail Sent by navigating to a Sent search URL
and reading the result rows (more reliable than typing into the search box)."""
import sys, time, json
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval
from urllib.parse import quote

email = sys.argv[1]
tabs = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
if not tabs:
    print("NO GMAIL TAB"); sys.exit(1)
tab = tabs[0]
ws = connect(tab)
cdp = make_cdp(ws)
cdp("Page.enable")
cdp("Page.bringToFront")
url = "https://mail.google.com/mail/u/0/#search/in%3Asent%20" + quote(email)
cdp("Page.navigate", {"url": url})
time.sleep(7)

res = js_eval(ws, """(() => {
  const body = document.body.innerText;
  const noMatch = /No emails matched|There are no emails/i.test(body);
  const rows = Array.from(document.querySelectorAll('div[role="main"] div[role="listitem"]'))
      .slice(0,5).map(r => (r.innerText||'').replace(/\\s+/g,' ').slice(0,170));
  return JSON.stringify({noMatch, rows, head: body.slice(0,200)});
})()""", await_promise=False)
print("SENT RESULT for", email, ":", res)
ws.close()
