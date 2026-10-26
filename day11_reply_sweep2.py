#!/usr/bin/env python3
"""Wider Gmail reply sweep: checks several query variants (last 2d, last 5d,
in:inbox, is:unread) and returns every inbound thread that is NOT from 'me'.
Read-only. Personal-contact senders are filtered out of the output."""
import sys, time, json, re
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

PERSONAL = re.compile(r'sayyam|shamas|afzal|chacho', re.I)
QUERIES = [
    "newer_than:3d -from:me -from:mailer-daemon@google.com -from:postmaster",
    "newer_than:7d -from:me -from:mailer-daemon@google.com -from:postmaster -from:noreply",
    "in:inbox newer_than:3d -from:me",
]

tabs = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
if not tabs:
    print(json.dumps({"error": "no gmail tab"})); sys.exit(1)
tab = tabs[0]
ws = connect(tab)
cdp = make_cdp(ws)
cdp("Page.enable")
cdp("Page.bringToFront")

all_items = []
for q in QUERIES:
    from urllib.parse import quote
    url = "https://mail.google.com/mail/u/0/#search/" + quote(q)
    cdp("Page.navigate", {"url": url})
    time.sleep(7)
    v = js_eval(ws, r"""(() => {
      const out = [];
      const rows = Array.from(document.querySelectorAll('div[role="main"] div[role="listitem"]'));
      for (const r of rows) {
        const t = (r.innerText || '').replace(/\s+/g, ' ').trim();
        if (!t) continue;
        const span = r.querySelector('span[email]');
        const from = span ? (span.getAttribute('email') || '') : '';
        const subjEl = r.querySelector('span[data-thread-subject]');
        const subject = subjEl ? (subjEl.innerText || '') : '';
        if (!from) continue;
        if (/mailer-daemon|postmaster|mail-daemon|noreply|no-reply|notifications@google/i.test(from)) continue;
        out.push({from: from, subject: subject.slice(0, 110), snippet: t.slice(0, 230)});
      }
      return JSON.stringify({n: rows.length, items: out.slice(0, 20)});
    })()""", await_promise=False)
    try:
        d = json.loads(v)
    except Exception:
        d = {"n": 0, "items": [], "raw": str(v)[:200]}
    for it in d.get("items", []):
        if PERSONAL.search(it["from"]):
            continue
        it["query"] = q
        all_items.append(it)
    print(f"query [{q}] -> rows={d.get('n')} inbound={len(d.get('items', []))}", file=sys.stderr)

# dedupe
seen = set()
uniq = []
for it in all_items:
    k = (it["from"], it["subject"])
    if k in seen:
        continue
    seen.add(k)
    uniq.append(it)
print(json.dumps({"count": len(uniq), "items": uniq}, indent=2, ensure_ascii=False))
ws.close()
