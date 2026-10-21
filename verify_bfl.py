#!/usr/bin/env python3
"""Post-send verification for Brazilian Fight Lisboa."""
import sys, time, json
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import *

tab = find_tab(lambda t: 'web.whatsapp' in t['url'] and t['type'] == 'page')
ws = connect(tab)
cdp = make_cdp(ws)
cdp("Page.navigate", {"url": "https://web.whatsapp.com/send?phone=351910349061"})
time.sleep(14)
v = js_eval(ws, '''(() => {
  const main = document.querySelector('#main');
  const t = main ? main.innerText : '';
  return JSON.stringify({
    header: t.slice(0, 22),
    landed: t.includes('Quantas peças precisam para começar'),
    signoff: t.includes('HSN Warrior Apparels'),
    tail: t.slice(-140).replace(/\\n/g, ' | ')
  });
})()''')
print(v)
ws.close()
