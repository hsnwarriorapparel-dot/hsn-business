import sys, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval

TARGET = sys.argv[1] if len(sys.argv) > 1 else 'TOWASAN'

tabs = get_tabs()
wa = [t for t in tabs if 'web.whatsapp.com' in (t.get('url') or '') and t.get('type') == 'page']
if not wa:
    print('NO WA TAB'); sys.exit(1)
ws = connect(wa[0])
js = """(()=>{
  const rows=[...document.querySelectorAll('[role="listitem"], [role="row"]')];
  const hit=rows.find(r=>((r.innerText||'')+' '+(r.textContent||'')).toLowerCase().includes(TARGET.toLowerCase()));
  if(!hit) return 'not-found';
  hit.click();
  return 'clicked';
})()""".replace('TARGET', repr(TARGET))
print('open:', js_eval(ws, js, await_promise=False))
time.sleep(13)
info = js_eval(ws, """(()=>{
  const grids=[...document.querySelectorAll('[role="grid"]')];
  const out=grids.map((g,i)=>({i, text:(g.innerText||'').slice(0,2500), rows:g.querySelectorAll('[role="row"]').length}));
  return {grids:out};
})()""", await_promise=False) or {}
for g in (info.get('grids') or []):
    print()
    print('=== GRID %s (rows=%s) ===' % (g.get('i'), g.get('rows')))
    print(g.get('text'))
ws.close()
