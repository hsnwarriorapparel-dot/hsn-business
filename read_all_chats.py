#!/usr/bin/env python3
"""Read all 5 active client chats fully for follow-up analysis."""
import sys, time, json
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import *

tab = find_tab(lambda t: 'web.whatsapp' in t['url'] and t['type'] == 'page')
ws = connect(tab)
cdp = make_cdp(ws)
cdp("Page.enable")

chats = [
    ("ALVARO (UAE)", "971504894282"),
    ("BRAZILIAN FIGHT LISBOA (PT)", "351910349061"),
    ("DURAMUK (PT)", "351967734557"),
    ("SCORPION (IT)", "393514088140"),
    ("LUCERO (ES)", "34633215305"),
]
for name, phone in chats:
    cdp("Page.navigate", {"url": f"https://web.whatsapp.com/send?phone={phone}"})
    time.sleep(14)
    v = js_eval(ws, '''(() => {
      const main = document.querySelector('#main');
      const t = main ? main.innerText : '';
      return t.slice(-700).replace(/\\n/g, ' | ');
    })()''')
    print(f"===== {name} =====")
    print(v[-660:])
    print()
ws.close()
