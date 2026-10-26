#!/usr/bin/env python3
"""Robust Gmail Sent verification: search URL + read the whole main panel text,
and count Drafts. Used to confirm a send actually LEFT the compose box."""
import sys, time, json
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval
from urllib.parse import quote

email = sys.argv[1] if len(sys.argv) > 1 else None
tabs = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
if not tabs:
    print("NO GMAIL TAB"); sys.exit(1)
tab = tabs[0]
ws = connect(tab)
cdp = make_cdp(ws)
cdp("Page.enable")
cdp("Page.bringToFront")

if email:
    url = "https://mail.google.com/mail/u/0/#search/in%3Asent%20" + quote(email)
    cdp("Page.navigate", {"url": url})
    time.sleep(8)

res = js_eval(ws, """(() => {
  const body = document.body.innerText;
  const drafts = (body.match(/Drafts\\s*(\\d+)/) || [])[1] || '0';
  const noMatch = /No emails matched|There are no emails/i.test(body);
  // grab the list container text
  const main = document.querySelector('div[role="main"]');
  const mt = main ? (main.innerText||'').replace(/\\s+/g,' ').slice(0,700) : '';
  return JSON.stringify({noMatch, drafts, mainText: mt, url: location.hash});
})()""", await_promise=False)
print("RESULT:", res)
ws.close()
