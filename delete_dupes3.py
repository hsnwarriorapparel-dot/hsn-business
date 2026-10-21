#!/usr/bin/env python3
"""Delete duplicates - the delete dialog opens; find its confirm button (aria-label scan)."""
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
      document.querySelectorAll('#main [role="row"]').forEach((m, i) => { if (m.innerText.includes(MARKER)) out.push(i); });
      return JSON.stringify(out);
    })()'''.replace('MARKER', json.dumps(marker)))
    idxs = json.loads(r)
    if len(idxs) < 2:
        return f"no dup (rows {idxs})"
    last = idxs[-1]
    js_eval(ws, f'''(() => {{
      const t = document.querySelectorAll('#main [role="row"]')[{last}];
      t.scrollIntoView({{block: 'center'}});
    }})()''')
    time.sleep(2)
    pos = json.loads(js_eval(ws, f'''(() => {{
      const t = document.querySelectorAll('#main [role="row"]')[{last}];
      const rect = t.getBoundingClientRect();
      return JSON.stringify({{x: Math.floor(rect.x + rect.width*0.5), y: Math.floor(rect.y + rect.height*0.5)}});
    }})()'''))
    cdp("Input.dispatchMouseEvent", {"type": "mousePressed", "x": pos['x'], "y": pos['y'], "button": "right", "clickCount": 1})
    cdp("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": pos['x'], "y": pos['y'], "button": "right", "clickCount": 1})
    time.sleep(2)
    js_eval(ws, '''(() => {
      const items = Array.from(document.querySelectorAll('[role="menuitem"]'));
      const del = items.find(el => (el.innerText||'').trim().toLowerCase().startsWith('delete'));
      if (del) del.click();
      return 'clicked';
    })()''')
    time.sleep(2)
    # dump EVERYTHING visible in dialogs for debugging
    debug = js_eval(ws, '''(() => {
      const out = [];
      document.querySelectorAll('[role="dialog"] *').forEach(el => {
        const t = (el.innerText||'').trim();
        if (t && t.length < 40 && el.children.length === 0) out.push(t);
      });
      return JSON.stringify(out.slice(0, 15));
    })()''')
    print("dialog contents:", debug)
    # try clicking the delete-for-everyone styled button (red text)
    ok3 = js_eval(ws, '''(() => {
      const cands = Array.from(document.querySelectorAll('[role="dialog"] [role="button"], [role="dialog"] div[tabindex]'));
      const btn = cands.find(el => (el.innerText||'').toLowerCase().includes('delete for everyone'));
      if (!btn) return 'not-found';
      btn.click();
      return 'clicked-confirm';
    })()''')
    print("confirm attempt:", ok3)
    time.sleep(4)
    final = js_eval(ws, '''(() => {
      let count = 0;
      document.querySelectorAll('#main [role="row"]').forEach(m => { if (m.innerText.includes(MARKER)) count++; });
      return count;
    })()'''.replace('MARKER', json.dumps(marker)))
    return f"remaining: {final}"

print("ALVARO:", try_delete("971504894282", "regarding content collaboration"))
print("SCORPION:", try_delete("393514088140", "I'll keep this short"))
ws.close()
