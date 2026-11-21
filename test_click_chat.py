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

# Replicate wa_send_open_chat.py search logic exactly
js = f"""(()=>{{
  const rows=[...document.querySelectorAll('[data-testid^="list-item-"]')];
  for(const it of rows){{
    const t=((it.innerText||'')+' '+(it.textContent||'')).toLowerCase();
    if(t.includes({json.dumps(LOW)})){{
      it.scrollIntoView({{block:'center', behavior:'instant'}});
      const rc=it.getBoundingClientRect();
      return JSON.stringify({{x:rc.x+rc.width/2, y:rc.y+rc.height/2}});
    }}
  }}
  return 'not-found';
}})()"""
pos = js_eval(ws, js, await_promise=False)
print('Position result:', pos)

if pos and pos != 'not-found':
    p = json.loads(pos)
    print(f'Clicking at x={p["x"]}, y={p["y"]}')
    for typ in ('mousePressed', 'mouseReleased'):
        cdp('Input.dispatchMouseEvent', {'type': typ, 'x': p['x'], 'y': p['y'], 'button': 'left', 'clickCount': 1})
    time.sleep(5)
    
    # Check if conversation opened
    st = js_eval(ws, """(()=>!!document.querySelector('[data-testid="conversation-compose-box-input"]'))()""", await_promise=False)
    print('Conversation opened:', st)

ws.close()