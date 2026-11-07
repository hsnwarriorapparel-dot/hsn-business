import sys, time, json
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval

tabs = get_tabs()
wa = [t for t in tabs if 'web.whatsapp.com' in (t.get('url') or '') and t.get('type') == 'page']
if not wa:
    print('NO WA TAB'); sys.exit(1)
ws = connect(wa[0])
js = """(()=>{
  const out={};
  out.pane = !!document.querySelector('#pane-side');
  out.main = !!document.querySelector('#main');
  // chat list rows
  const rows=[...document.querySelectorAll('[role="listitem"], [role="row"]')];
  out.rows = rows.length;
  out.sample = rows.slice(0,12).map(r=>(r.innerText||'').replace(/\\n/g,' | ').slice(0,80)).filter(Boolean);
  // composer inputs
  out.inputs = [...document.querySelectorAll('[contenteditable="true"], textarea')].map(e=>e.getAttribute('aria-label')||e.tagName).slice(0,8);
  // "unread" badge numbers
  const badges=[...document.querySelectorAll('[aria-label*="unread" i]')].map(e=>(e.getAttribute('aria-label')||'').slice(0,40));
  out.badges=badges.slice(0,8);
  return out;
})()"""
info = js_eval(ws, js, await_promise=False) or {}
print('chat pane (#pane-side):', info.get('pane'))
print('main area (#main)     :', info.get('main'))
print('chat list rows        :', info.get('rows'))
print('composer inputs       :', info.get('inputs'))
print('unread badges         :', info.get('badges'))
print()
print('--- chat list sample ---')
for s in (info.get('sample') or []):
    print('  ', s)
ws.close()
