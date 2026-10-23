#!/usr/bin/env python3
"""Sprint Day 1: extract the 7 hottest Tradewheel RFQs via CDP browser (full URLs now known)."""
import sys, time, json
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import *

RFQ_URLS = [
    "https://www.tradewheel.com/buyers/inquiry-for-martial-arts-uniforms-requesting-quotes/1008078/",
    "https://www.tradewheel.com/buyers/finding-businesses-selling-rash-guards-and-compression-sportswear/973870/",
    "https://www.tradewheel.com/buyers/in-need-of-martial-arts-uniforms-from-manufacturer/970198/",
    "https://www.tradewheel.com/buyers/need-martial-arts-urgently/953573/",
    "https://www.tradewheel.com/buyers/looking-for-martial-arts-wear-with-custom-specs/939695/",
    "https://www.tradewheel.com/buyers/sourcing-pearl-weave-and-ripstop-fabrics-for-martial/998662/",
    "https://www.tradewheel.com/buyers/seeking-water-filled-taekwondo-punching-dummy-for-martial-arts/1024395/",
]

tab = find_tab(lambda t: t['type'] == 'page' and ('whatsapp' in t['url'] or 'instagram' in t['url'] or 'google' in t['url']))
ws = connect(tab)
cdp = make_cdp(ws)
cdp("Page.enable")

rfqs = []
for u in RFQ_URLS:
    cdp("Page.navigate", {"url": u})
    time.sleep(13)
    v = js_eval(ws, '''(() => {
      const t = document.body ? document.body.innerText : '';
      const emails = [...new Set([...t.matchAll(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}/g)].map(m => m[0]))].slice(0, 3);
      const qty = (t.match(/(\\d[\\d,]{0,8})\\s*(?:pieces|pcs|units|Piece)/i) || [])[1] || '';
      const country = (t.match(/(?:Country|Location|From)[:\\s\\n]+([A-Za-z .]{3,22})/) || [])[1] || '';
      const posted = (t.match(/(?:Posted on|Date)[:\\s]*([A-Za-z0-9,\\s]{6,24})/) || [])[1] || '';
      const contactBtn = !!document.querySelector('a[href*="contact"], button');
      const desc = t.replace(/\\s+/g, ' ').slice(0, 400);
      return JSON.stringify({title: document.title.slice(0, 90), emails: emails, qty: qty,
                             country: country.trim(), posted: posted.trim(), desc: desc});
    })()''')
    try:
        d = json.loads(v)
    except Exception:
        d = {'title': 'PARSE-FAIL', 'emails': [], 'qty': '', 'country': '', 'posted': '', 'desc': ''}
    d['url'] = u
    rfqs.append(d)
    print(f"  {d['title'][:60]}")
    print(f"    qty: {d['qty']} | country: {d['country'][:18]} | emails: {d['emails'][:2]} | posted: {d['posted'][:18]}")

json.dump(rfqs, open('/home/ubuntu/rfq_harvest_day1.json', 'w'), indent=1)
ws.close()
print(f"\nSAVED {len(rfqs)} RFQs to /home/ubuntu/rfq_harvest_day1.json")
