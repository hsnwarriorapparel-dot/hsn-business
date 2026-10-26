#!/usr/bin/env python3
"""Day-11 foreground test send: ONE email to the first wave lead.
Prints the rendered subject/body and the RAW return value of gmail_send
(skill rule: senders return different shapes - gmail_send returns the string 'sent').
Also verifies the message actually left compose (dialog gone) and appears in Sent.
"""
import sys, time, csv, json
sys.path.insert(0, '/home/ubuntu')
from outreach import gmail_send
from templates import build_email
from cdp_helper import get_tabs, connect, js_eval

LEAD_ID = sys.argv[1] if len(sys.argv) > 1 else None
CSV = '/home/ubuntu/leads.csv'
rows = list(csv.reader(open(CSV, encoding='utf-8', errors='replace')))
idx = {h: i for i, h in enumerate(rows[0])}
iE, iS, iN, iC, iCi = (idx['Email'], idx['Status'], idx['Name'], idx['Country'], idx['City'])

target = None
for r in rows[1:]:
    if len(r) <= iS:
        continue
    if LEAD_ID and r[0] != LEAD_ID:
        continue
    st = (r[iS] or '').lower()
    if 'email sent' in st or 'excluded' in st:
        continue
    target = r
    break

if not target:
    print("no target row found"); sys.exit(1)

lid = target[0]
name = (target[iN] or '').strip().replace('&', 'and')
email = (target[iE] or '').strip().lower()
country = (target[iC] or '').strip() or 'Europe'
city = (target[iCi] or '').strip()
region = 'USA' if country == 'USA' else 'Europe'
detail = f"martial arts and boxing gym in {city}" if city else f"martial arts and boxing gym in {country}"

subject, body = build_email(name, detail, region=region)
print("LEAD:", lid, "|", name, "|", email, "|", country, city)
print("--- SUBJECT ---"); print(subject)
print("--- BODY ---"); print(body)
print("--- sending ---")

t0 = time.time()
res = gmail_send(email, subject, body)
print("RAW RETURN:", repr(res), "| type:", type(res).__name__, "| secs:", round(time.time() - t0, 1))
ok = res.get('ok') if isinstance(res, dict) else ('sent' in str(res).lower())
print("OK CHECK ->", bool(ok))

# verify: our compose dialog is gone + Sent folder shows the recipient
tabs = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
if tabs:
    ws = connect(tabs[0])
    v = js_eval(ws, """(() => {
      const ours = document.querySelector('div[data-hsn-compose]');
      const body = document.body ? document.body.innerText : '';
      return JSON.stringify({composeStillOpen: !!ours, bodyHasRecipient: body.toLowerCase().includes(%s.toLowerCase())});
    })()""" % repr(email), await_promise=False)
    print("VERIFY:", v)
    ws.close()
else:
    print("VERIFY: no gmail tab")
