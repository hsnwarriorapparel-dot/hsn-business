#!/usr/bin/env python3
"""Sanity check for the reply sweep: read the raw inbox list WITHOUT filters and
show what is actually there (so '0 inbound' can be trusted, not a broken selector)."""
import sys, time, json
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

tabs = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
if not tabs:
    print("NO GMAIL TAB"); sys.exit(1)
tab = tabs[0]
ws = connect(tab)
cdp = make_cdp(ws)
cdp("Page.enable")
cdp("Page.bringToFront")
cdp("Page.navigate", {"url": "https://mail.google.com/mail/u/0/#inbox"})
time.sleep(8)

v = js_eval(ws, r"""(() => {
  const rows = Array.from(document.querySelectorAll('div[role="main"] div[role="listitem"]'));
  const items = rows.slice(0, 20).map(r => {
    const span = r.querySelector('span[email]');
    const from = span ? (span.getAttribute('email') || '') : '';
    const subjEl = r.querySelector('span[data-thread-subject]');
    const subject = subjEl ? (subjEl.innerText || '') : '';
    return {from, subject: subject.slice(0,80), raw: (r.innerText||'').replace(/\s+/g,' ').slice(0,150)};
  });
  const main = document.querySelector('div[role="main"]');
  return JSON.stringify({n: rows.length, items, mainHead: main ? (main.innerText||'').slice(0,200) : 'no-main'});
})()""", await_promise=False)
d = json.loads(v)
print("inbox rows readable:", d["n"])
for it in d["items"]:
    tag = "INBOUND" if it["from"] and "me" not in it["from"] else "from-me/other"
    print(f"  [{tag}] from={it['from'][:38]:38} | {it['subject'][:60]}")
print("\nmain head:", d["mainHead"])
ws.close()
