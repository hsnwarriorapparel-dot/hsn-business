#!/usr/bin/env python3
"""Delete duplicates via message context menu: click message body -> right side menu."""
import sys, time, json
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import *

tab = find_tab(lambda t: 'web.whatsapp' in t['url'] and t['type'] == 'page')
ws = connect(tab)
cdp = make_cdp(ws)
cdp("Page.enable")

def try_delete(phone, marker):
    cdp("Page.navigate", {"url": f"https://web.whatsapp.com/send?phone={phone}"})
    time.sleep(14)
    r = js_eval(ws, '''(() => {
      const out = [];
      const msgs = document.querySelectorAll('#main [role="row"]');
      msgs.forEach((m, i) => { if (m.innerText.includes(MARKER)) out.push(i); });
      return JSON.stringify(out);
    })()'''.replace('MARKER', json.dumps(marker)))
    idxs = json.loads(r)
    if len(idxs) < 2:
        return f"no dup (rows {idxs})"
    last = idxs[-1]
    # scroll the duplicate into view and RIGHT-CLICK it to open the context menu
    js_eval(ws, '''(() => {
      const msgs = document.querySelectorAll('#main [role="row"]');
      const t = msgs[IDX];
      t.scrollIntoView({block: 'center'});
    })()'''.replace('IDX', str(last)))
    time.sleep(2)
    box = js_eval(ws, '''(() => {
      const msgs = document.querySelectorAll('#main [role="row"]');
      const t = msgs[IDX];
      const rect = t.getBoundingClientRect();
      return JSON.stringify({x: Math.floor(rect.x + rect.width*0.5), y: Math.floor(rect.y + rect.height*0.5)});
    })()'''.replace('IDX', str(last)))
    pos = json.loads(box)
    # right-click at position (CDP Input.dispatchMouseEvent)
    cdp("Input.dispatchMouseEvent", {"type": "mousePressed", "x": pos['x'], "y": pos['y'], "button": "right", "clickCount": 1})
    cdp("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": pos['x'], "y": pos['y'], "button": "right", "clickCount": 1})
    time.sleep(2)
    m = js_eval(ws, '''(() => {
      const items = Array.from(document.querySelectorAll('[role="menuitem"]'));
      return JSON.stringify(items.map(el => (el.innerText||'').trim().slice(0,20)));
    })()''')
    print("menu items:", m)
    ok2 = js_eval(ws, '''(() => {
      const items = Array.from(document.querySelectorAll('[role="menuitem"]'));
      const del = items.find(el => (el.innerText||'').trim().toLowerCase().startsWith('delete'));
      if (!del) return 'no-delete';
      del.click();
      return 'delete-clicked';
    })()''')
    print("delete:", ok2)
    if ok2 != 'delete-clicked':
        return 'fail-menu'
    time.sleep(2)
    ok3 = js_eval(ws, '''(() => {
      const items = Array.from(document.querySelectorAll('[role="button"]'));
      const btn = items.find(el => (el.innerText||'').trim().toLowerCase().includes('delete for everyone'));
      if (!btn) return 'no-confirm';
      btn.click();
      return 'confirmed';
    })()''')
    print("confirm:", ok3)
    time.sleep(4)
    final = js_eval(ws, '''(() => {
      let count = 0;
      document.querySelectorAll('#main [role="row"]').forEach(m => { if (m.innerText.includes(MARKER)) count++; });
      return count;
    })()'''.replace('MARKER', json.dumps(marker)))
    return f"remaining copies: {final}"

print("ALVARO:", try_delete("971504894282", "regarding content collaboration"))
print("SCORPION:", try_delete("393514088140", "I'll keep this short"))
ws.close()
