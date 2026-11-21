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

opened = False
for attempt in range(4):
    print(f'Attempt {attempt+1}')
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
    print(f'  Position: {pos}')
    if not pos or pos == 'not-found':
        break
    try:
        p = json.loads(pos)
    except Exception as e:
        print(f'  JSON parse error: {e}')
        break
    time.sleep(1.2)
    
    # Re-check position
    pos2 = js_eval(ws, js, await_promise=False)
    print(f'  Position2: {pos2}')
    try:
        p2 = json.loads(pos2)
    except Exception as e:
        print(f'  JSON parse error2: {e}')
        break
    
    for typ in ('mousePressed', 'mouseReleased'):
        cdp('Input.dispatchMouseEvent', {'type': typ, 'x': p2['x'], 'y': p2['y'], 'button': 'left', 'clickCount': 1})
    time.sleep(7)
    
    st = js_eval(ws, """(()=>!!document.querySelector('[data-testid="conversation-compose-box-input"]'))()""", await_promise=False)
    print(f'  Conversation opened: {st}')
    if st:
        opened = True
        break

if not opened:
    print('FAILED TO OPEN CONVERSATION')
else:
    print('SUCCESS: Conversation opened')
    # Now type and send message
    MSG = open('/home/ubuntu/shudokan_nudge_wa.txt', encoding='utf-8').read()
    print(f'Message length: {len(MSG)}')
    
    # Type message
    js_eval(ws, 'window.__waMsg = ' + json.dumps(MSG) + '; window.__waMsg.length', await_promise=False)
    typed = js_eval(ws, r"""(()=>{
      const msg = window.__waMsg || '';
      const inp=document.querySelector('[data-testid="conversation-compose-box-input"]') ||
                document.querySelector('div[contenteditable="true"][data-tab="10"]');
      if(!inp) return 'no-composer';
      inp.focus();
      const proto = Object.getPrototypeOf(inp);
      const desc = Object.getOwnPropertyDescriptor(proto, 'textContent');
      if(desc && desc.set) desc.set.call(inp, msg);
      else inp.textContent = msg;
      inp.dispatchEvent(new InputEvent('input',{bubbles:true, inputType:'insertText', data:msg}));
      inp.dispatchEvent(new Event('change',{bubbles:true}));
      return 'typed:'+msg.length+':'+(inp.textContent||'').length;
    })()""", await_promise=False)
    print('Type result:', typed)
    time.sleep(2.5)
    
    # Send
    sent = js_eval(ws, r"""(()=>{
      const btn=document.querySelector('[data-testid="compose-btn-send"]') ||
                document.querySelector('span[data-icon="send"]') ||
                document.querySelector('button[aria-label="Send"]');
      if(!btn) return 'no-send-button';
      btn.click();
      return 'clicked-send';
    })()""", await_promise=False)
    print('Send result:', sent)
    time.sleep(5)
    
    # Verify
    after = js_eval(ws, r"""(()=>{
      const inp=document.querySelector('[data-testid="conversation-compose-box-input"]');
      const v=inp?((inp.value!==undefined && inp.value!==null && inp.value!=='' ? inp.value : (inp.textContent||''))||''):'';
      const rs=[...document.querySelectorAll('[role="row"]')]
        .map(r=>(r.innerText||r.textContent||'').trim()).filter(t=>t.length>4);
      return JSON.stringify({composerEmpty:v.trim().length===0, tail:rs.slice(-3)});
    })()""", await_promise=False)
    print('After send:', after)

ws.close()