#!/usr/bin/env python3
"""Delete the duplicate messages in Alvaro + Scorpion chats (delete for everyone)."""
import sys, time, json
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import *

tab = find_tab(lambda t: 'web.whatsapp' in t['url'] and t['type'] == 'page')
ws = connect(tab)
cdp = make_cdp(ws)
cdp("Page.enable")

def delete_last_duplicate(phone, marker):
    cdp("Page.navigate", {"url": f"https://web.whatsapp.com/send?phone={phone}"})
    time.sleep(14)
    # 1. find all message bubbles containing the marker; take the LAST one, open its menu
    r = js_eval(ws, '''(() => {
      const out = [];
      const msgs = document.querySelectorAll('#main [role="row"]');
      msgs.forEach((m, i) => {
        if (m.innerText.includes(MARKER)) out.push(i);
      });
      return JSON.stringify(out);
    })()'''.replace('MARKER', json.dumps(marker)))
    idxs = json.loads(r)
    print("matching rows:", idxs)
    if len(idxs) < 2:
        return "no duplicate found"
    # 2. hover over the LAST matching message to reveal the chevron, click it
    ok = js_eval(ws, '''(() => {
      const msgs = document.querySelectorAll('#main [role="row"]');
      const target = msgs[IDX];
      target.scrollIntoView({block: 'center'});
      const chev = target.querySelector('[data-icon="chevron-down"]') || target.querySelector('span[data-icon="chevron-down"]');
      if (!chev) return 'no-chevron';
      chev.click();
      return 'clicked';
    })()'''.replace('IDX', str(idxs[-1])))
    print("chevron:", ok)
    if ok != 'clicked':
        return 'failed-chevron'
    time.sleep(2)
    # 3. click "Delete" in the popup menu
    ok2 = js_eval(ws, '''(() => {
      const items = Array.from(document.querySelectorAll('[role="menuitem"], [role="button"]'));
      const del = items.find(el => (el.innerText||'').trim().toLowerCase().startsWith('delete'));
      if (!del) return 'no-delete-item';
      del.click();
      return 'delete-clicked';
    })()''')
    print("delete item:", ok2)
    if ok2 != 'delete-clicked':
        return 'failed-delete-item'
    time.sleep(2)
    # 4. confirm "Delete for everyone" in the dialog
    ok3 = js_eval(ws, '''(() => {
      const items = Array.from(document.querySelectorAll('[role="button"]'));
      const btn = items.find(el => (el.innerText||'').trim().toLowerCase().includes('delete for everyone'));
      if (!btn) return 'no-confirm';
      btn.click();
      return 'confirmed';
    })()''')
    print("confirm:", ok3)
    time.sleep(4)
    # 5. verify only 1 copy remains
    final = js_eval(ws, '''(() => {
      let count = 0;
      document.querySelectorAll('#main [role="row"]').forEach(m => { if (m.innerText.includes(MARKER)) count++; });
      return JSON.stringify({remaining: count});
    })()'''.replace('MARKER', json.dumps(marker)))
    return f"final: {final}"

print("ALVARO:", delete_last_duplicate("971504894282", "regarding content collaboration"))
print("SCORPION:", delete_last_duplicate("393514088140", "I'll keep this short"))
ws.close()
