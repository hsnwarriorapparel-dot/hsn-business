import sys, time, json
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval

tabs = get_tabs()
ig = [t for t in tabs if 'instagram.com/direct' in t.get('url', '') and t.get('type') == 'page']
if not ig:
    ig = [t for t in tabs if 'instagram.com' in t.get('url', '') and t.get('type') == 'page']
if not ig:
    print('NO IG TAB'); sys.exit(1)
ws = connect(ig[0])
# dump the visible text of the left thread pane
info = js_eval(ws, """(()=>{
  const out={};
  out.anchors=[...document.querySelectorAll('a')].slice(0,40).map(a=>({h:(a.getAttribute('href')||'').slice(0,50),t:(a.textContent||'').trim().replace(/\\s+/g,' ').slice(0,60)}));
  const pane=document.querySelector('div[role="main"]');
  out.text=pane?(pane.innerText||'').slice(0,1800):'';
  return out;
})()""", await_promise=False) or {}
print('=== anchors ===')
for a in (info.get('anchors') or [])[:25]:
    if a.get('t'):
        print('  %-48s | %s' % (a.get('h'), a.get('t')))
print()
print('=== pane text ===')
print((info.get('text') or '')[:1500])
ws.close()
