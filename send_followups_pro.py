#!/usr/bin/env python3
"""Send 4 professional follow-ups with verify-first protocol."""
import sys, time, json
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import *
from outreach import wa_send

jobs = [
    ("Duramuk_ONLY", "351967734557", "SKIP"),
    ("Lucero_ONLY", "34633215305", "SKIP"),
    ("Alvaro", "971504894282", """Alvaro, regarding content collaboration — we work with trainers on a simple model: you receive our gear with your own branding, create training content with it, and we support you with priority production and partner pricing on future orders.

The first step is the same sample set we discussed — €77.40, everything included. Send me your logo and I'll show you the mockup before anything else."""),
    ("Duramuk", "351967734557", """Hello Team Duramuk! To give you an exact quote, we prepare both versions — training construction and competition construction — with your logo, so you can compare quality and price side by side.

For a clear comparison: how many athletes does your team currently equip?"""),
    ("Scorpion", "393514088140", """Hello Scorpion Boxing. I'll keep this short — we manufacture boxing gloves, pads and apparel with gym branding, from €19.50 per unit at factory prices, and we ship to Italy with no customs costs.

If equipping your gym is on your plans this season, reply to this message and I'll prepare a full quote same day. Wishing your athletes a strong season."""),
    ("Lucero", "34633215305", """Hello Lucero. As a Muay Thai gym, your three highest-margin items are Thai pads, fight shorts and gloves — all three we manufacture with your gym's branding, with photos of real client orders available on request.

If you send me your team size, I'll prepare an exact quote for a complete starter set this week."""),
]

results = []
for name, phone, msg in jobs:
    if msg == "SKIP":
        continue
    # STEP 1: header + history verify BEFORE sending
    tab = find_tab(lambda t: 'web.whatsapp' in t['url'] and t['type'] == 'page')
    ws = connect(tab)
    cdp = make_cdp(ws)
    cdp("Page.enable")
    cdp("Page.navigate", {"url": f"https://web.whatsapp.com/send?phone={phone}"})
    time.sleep(15)
    v = js_eval(ws, '''(() => {
      const main = document.querySelector('#main');
      const t = main ? main.innerText : '';
      return JSON.stringify({header: t.slice(0, 40)});
    })()''')
    d = json.loads(v)
    ws.close()
    names = {'Alvaro': 'Álvaro', 'Duramuk': 'Team Duramuk', 'Scorpion': '351 408 8140', 'Lucero': 'Lucero Muay Thai'}
    ok_header = phone[-9:] in d['header'].replace(' ', '') or names.get(name, '') in d['header']
    print(f"{name} STEP1 header: {d['header'][:30]} -> {'OK' if ok_header else 'ABORT'}")
    if not ok_header:
        continue
    # STEP 2: send
    r = wa_send(phone, msg)
    ok = '"ok":true' in str(r)
    print(f"{name} STEP2 send: {'OK' if ok else str(r)[:60]}")
    results.append((name, ok))
    time.sleep(20)

print("\nSUMMARY:", results)
