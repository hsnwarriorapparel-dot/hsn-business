import sys, json, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval, make_cdp

tabs = get_tabs()
wa = [t for t in tabs if 'web.whatsapp.com' in (t.get('url') or '') and t.get('type') == 'page']
if not wa:
    print('NO WA TAB')
    sys.exit(1)
ws = connect(wa[0])
cdp = make_cdp(ws)

TARGET = "+34 661 57 14 63"
LOW = TARGET.lower()

# Try clicking the cell-frame-container element
js = f"""(()=>{{
  const rows=[...document.querySelectorAll('[data-testid^="list-item-"]')];
  for(const it of rows){{
    const t=((it.innerText||'')+' '+(it.textContent||'')).toLowerCase();
    if(t.includes({json.dumps(LOW)})){{
      const cell = it.querySelector('[data-testid="cell-frame-container"]');
      if(cell) {{
        cell.scrollIntoView({{block:'center', behavior:'instant'}});
        cell.click();
        return 'clicked-cell-frame';
      }}
      const gridcell = it.querySelector('[role="gridcell"]');
      if(gridcell) {{
        gridcell.scrollIntoView({{block:'center', behavior:'instant'}});
        gridcell.click();
        return 'clicked-gridcell-fallback';
      }}
      it.click();
      return 'clicked-row-fallback';
    }}
  }}
  return 'not-found';
}})()"""
result = js_eval(ws, js, await_promise=False)
print('Click result:', result)

time.sleep(5)

# Check if conversation opened
st = js_eval(ws, """(()=>!!document.querySelector('[data-testid="conversation-compose-box-input"]'))()""", await_promise=False)
print('Conversation opened:', st)

if not st:
    # Check main area
    info = js_eval(ws, """(()=>({
      main: !!document.querySelector('#main'),
      selectedChat: document.querySelector('[aria-selected="true"]') ? 'yes' : 'no'
    }))()""", await_promise=False)
    print('Page state:', info)

ws.close()