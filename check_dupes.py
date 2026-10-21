#!/usr/bin/env python3
"""Check if Alvaro + Scorpion got duplicate messages."""
import sys, time, json
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import *

tab = find_tab(lambda t: 'web.whatsapp' in t['url'] and t['type'] == 'page')
ws = connect(tab)
cdp = make_cdp(ws)
cdp("Page.enable")

checks = [
    ("Alvaro", "971504894282", "regarding content collaboration"),
    ("Scorpion", "393514088140", "I'll keep this short"),
]
for name, phone, marker in checks:
    cdp("Page.navigate", {"url": f"https://web.whatsapp.com/send?phone={phone}"})
    time.sleep(13)
    v = js_eval(ws, f'''(() => {{
      const main = document.querySelector('#main');
      const t = main ? main.innerText : '';
      const count = (t.match(/{marker}/g) || []).length;
      return JSON.stringify({{name: {name!r}, copies: count}});
    }})()''')
    print(v)
ws.close()
