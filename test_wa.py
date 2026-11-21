import sys, json
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval

tabs = get_tabs()
wa = [t for t in tabs if 'web.whatsapp.com' in (t.get('url') or '') and t.get('type') == 'page']
if not wa:
    print('NO WA TAB')
    sys.exit(1)
ws = connect(wa[0])

import time
time.sleep(1)

js = """(()=>{
  const rows=[...document.querySelectorAll('[role="listitem"], [role="row"]')];
  return JSON.stringify(rows.map(r=>(r.innerText||'').replace(/\\n/g,' | ').slice(0,200)).filter(Boolean));
})"""
all_rows = js_eval(ws, js, await_promise=False) or '[]'
rows = json.loads(all_rows)
print('Total rows:', len(rows))
for i, row in enumerate(rows):
    print(f'{i}: {row}')
ws.close()