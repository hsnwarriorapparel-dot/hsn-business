#!/usr/bin/env python3
"""Gmail reply sweep v2 — uses the CORRECT row selector.
The list rows are not div[role=listitem]; they carry span[email] elements.
Read-only, filters personal contacts, never sends."""
import sys, time, json, re
from urllib.parse import quote
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

PERSONAL = re.compile(r'sayyam|shamas|afzal|chacho', re.I)
AUTOMAIL = re.compile(r'mailer-daemon|postmaster|mail-daemon|noreply|no-reply|'
                      r'notifications@google|support@|bounce', re.I)

JS = r"""(() => {
  const spans = Array.from(document.querySelectorAll('span[email]'));
  const seen = new Set();
  const out = [];
  for (const s of spans) {
    const from = s.getAttribute('email') || '';
    if (!from || seen.has(from)) continue;
    seen.add(from);
    let row = s.closest('div[role="listitem"]') || s.closest('div.adn.ads') ||
              s.closest('tr') || s.closest('div');
    const txt = row ? (row.innerText || '').replace(/\s+/g, ' ').trim() : '';
    const subjEl = row ? row.querySelector('span[data-thread-subject]') : null;
    const subject = subjEl ? (subjEl.innerText || '') : '';
    out.push({from: from, subject: subject.slice(0, 120), snippet: txt.slice(0, 240)});
  }
  const main = document.querySelector('div[role="main"]');
  return JSON.stringify({spans: spans.length, items: out.slice(0, 40),
    mainHead: main ? (main.innerText || '').replace(/\s+/g,' ').slice(0, 180) : ''});
})()"""

tabs = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
if not tabs:
    print(json.dumps({"error": "no gmail tab"})); sys.exit(1)
tab = tabs[0]
ws = connect(tab)
cdp = make_cdp(ws)
cdp("Page.enable")
cdp("Page.bringToFront")

QUERIES = [
    "newer_than:3d -from:me -from:mailer-daemon@google.com -from:postmaster -from:noreply",
    "newer_than:7d -from:me -from:mailer-daemon@google.com -from:postmaster -from:noreply",
]
out_all = []
for q in QUERIES:
    cdp("Page.navigate", {"url": "https://mail.google.com/mail/u/0/#search/" + quote(q)})
    time.sleep(8)
    v = js_eval(ws, JS, await_promise=False)
    try:
        d = json.loads(v)
    except Exception:
        print("PARSE FAIL", str(v)[:200]); continue
    print(f"[{q}] spans={d.get('spans')} | head: {d.get('mainHead','')[:110]}", file=sys.stderr)
    for it in d.get("items", []):
        if PERSONAL.search(it["from"]):
            continue
        if AUTOMAIL.search(it["from"]):
            continue
        it["query"] = q
        out_all.append(it)

# dedupe by (from, subject)
seen = set()
uniq = []
for it in out_all:
    k = (it["from"], it["subject"])
    if k in seen:
        continue
    seen.add(k)
    uniq.append(it)
print(json.dumps({"count": len(uniq), "items": uniq}, indent=2, ensure_ascii=False))
ws.close()
