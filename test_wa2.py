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
  const out={};
  out.pane = !!document.querySelector('#pane-side');
  out.main = !!document.querySelector('#main');
  const rows=[...document.querySelectorAll('[role="listitem"], [role="row"]')];
  out.rows = rows.length;
  out.sample = rows.slice(0,50).map(r=>(r.innerText||'').replace(/\\n/g,' | ').slice(0,200)).filter(Boolean);
  return out;
})()"""
info = js_eval(ws, js, await_promise=False) or {}
print('pane:', info.get('pane'))
print('main:', info.get('main'))
print('rows:', info.get('rows'))
for s in (info.get('sample') or []):
    print('  ', s)
ws.close()