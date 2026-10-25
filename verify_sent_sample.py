#!/usr/bin/env python3
"""Independent verification that today's wave actually landed in Gmail Sent.
Samples N recipients from the wave file, searches Gmail Sent for each, and
reports how many are confirmed present (vs only marked in the CSV)."""
import sys, time, json, csv, random
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval
from urllib.parse import quote

N = int(sys.argv[1]) if len(sys.argv) > 1 else 6
WAVE = '/home/ubuntu/day11_wave.txt'
CSV = '/home/ubuntu/leads.csv'

ids = [l.strip() for l in open(WAVE) if l.strip()]
rows = list(csv.reader(open(CSV, encoding='utf-8', errors='replace')))
idx = {h: i for i, h in enumerate(rows[0])}
iE = idx['Email']
mail = {}
for r in rows[1:]:
    if r and r[0] in ids:
        mail[r[0]] = (r[iE] or '').strip().lower()

random.seed(11)
sample = random.sample(ids, min(N, len(ids)))

tabs = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
if not tabs:
    print("NO GMAIL TAB"); sys.exit(1)
tab = tabs[0]
ws = connect(tab)
cdp = make_cdp(ws)
cdp("Page.enable")
cdp("Page.bringToFront")

found = missing = 0
for lid in sample:
    email = mail.get(lid, '')
    url = "https://mail.google.com/mail/u/0/#search/in%3Asent%20" + quote(email)
    cdp("Page.navigate", {"url": url})
    time.sleep(6)
    v = js_eval(ws, r"""(() => {
      const m = document.querySelector('div[role="main"]');
      const t = m ? (m.innerText||'') : '';
      const hit = t.includes('Conversations') && t.toLowerCase().includes(%s.toLowerCase());
      const noMatch = /No emails matched|There are no emails/i.test(t);
      return JSON.stringify({hit, noMatch, snippet: t.replace(/\s+/g,' ').slice(120, 330)});
    })()""" % repr(email), await_promise=False)
    try:
        d = json.loads(v)
    except Exception:
        d = {"hit": False, "snippet": v}
    ok = d.get("hit")
    print(("CONFIRMED " if ok else "MISSING   ") + lid, "|", email, "|", d.get("snippet", "")[:150])
    if ok:
        found += 1
    else:
        missing += 1

print(f"\nSENT VERIFICATION: {found}/{len(sample)} sampled wave emails confirmed in Gmail Sent"
      f" ({missing} not found)")
ws.close()
