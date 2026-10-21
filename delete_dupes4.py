#!/usr/bin/env python3
"""Delete duplicate via keyboard: focus message row, open menu with chevron on hover (Input events)."""
import sys, time, json
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import *

tab = find_tab(lambda t: 'web.whatsapp' in t['url'] and t['type'] == 'page')
ws = connect(tab)
cdp = make_cdp(ws)
cdp("Page.enable")
cdp("DOM.enable")

def try_delete(phone, frag):
    cdp("Page.navigate", {"url": f"https://web.whatsapp.com/send?phone={phone}"})
    time.sleep(14)
    idxs = json.loads(js_eval(ws, '''(() => {
      const out = [];
      document.querySelectorAll('#main [role="row"]').forEach((m, i) => { if ((m.innerText||'').includes(FRAG)) out.push(i); });
      return JSON.stringify(out);
    })()'''.replace('FRAG', json.dumps(frag))))
    print("rows:", idxs)
    if len(idxs) < 2:
        return "no dup"
    last = idxs[-1]
    pos = json.loads(js_eval(ws, f'''(() => {{
      const t = document.querySelectorAll('#main [role="row"]')[{last}];
      t.scrollIntoView({{block: 'center'}});
      const rect = t.getBoundingClientRect();
      return JSON.stringify({{x: Math.floor(rect.x + rect.width*0.5), y: Math.floor(rect.y + rect.height*0.5)}});
    }})()'''))
    time.sleep(1)
    # HOVER over the message to make the chevron appear, then click it (left click on chevron zone)
    cdp("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": pos['x'], "y": pos['y']})
    time.sleep(1)
    chev = js_eval(ws, f'''(() => {{
      const rows = document.querySelectorAll('#main [role="row"]');
      const t = rows[{last}];
      const c = t.querySelector('[data-icon="chevron-down"]');
      if (!c) return 'no-chevron';
      const r = c.getBoundingClientRect();
      return JSON.stringify({{x: Math.floor(r.x + r.width/2), y: Math.floor(r.y + r.height/2)}});
    }})()''')
    print("chevron:", chev)
    if chev == 'no-chevron':
        return 'no-chevron'
    p = json.loads(chev)
    cdp("Input.dispatchMouseEvent", {"type": "mousePressed", "x": p['x'], "y": p['y'], "button": "left", "clickCount": 1})
    cdp("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": p['x'], "y": p['y'], "button": "left", "clickCount": 1})
    time.sleep(2)
    d = js_eval(ws, '''(() => {
      const items = Array.from(document.querySelectorAll('[role="menuitem"]'));
      const del = items.find(el => (el.innerText||'').trim().toLowerCase().startsWith('delete'));
      if (!del) return 'no-delete';
      del.click();
      return 'clicked';
    })()''')
    print("delete menu:", d)
    time.sleep(2)
    c = js_eval(ws, '''(() => {
      const cands = Array.from(document.querySelectorAll('div[role="dialog"] [role="button"], [role="dialog"] button, footer button, [data-animate-modal-body] button'));
      const txts = cands.map(el => (el.innerText||'').trim());
      const btn = cands.find(el => (el.innerText||'').toLowerCase().includes('everyone'));
      if (btn) { btn.click(); return 'clicked-everyone'; }
      return 'options: ' + JSON.stringify(txts.slice(0,5));
    })()''')
    print("confirm:", c)
    time.sleep(4)
    remaining = json.loads(js_eval(ws, '''(() => {
      let n = 0;
      document.querySelectorAll('#main [role="row"]').forEach(m => { if ((m.innerText||'').includes(FRAG)) n++; });
      return n;
    })()'''.replace('FRAG', json.dumps(frag))))
    return f"remaining: {remaining}"

print("ALVARO:", try_delete("971504894282", "Send me your logo"))
print("SCORPION:", try_delete("393514088140", "full quote same day"))
ws.close()
