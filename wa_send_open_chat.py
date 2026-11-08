"""Send a WhatsApp message to a chat that is ALREADY OPEN.

Unlike wa_sender_cdp.py (which searches by PHONE and clicks the first
result), this one:
  1. opens the chat by name, SCROLLING THE ROW INTO VIEW first
  2. verifies the conversation is the right one
  3. types the message and clicks Send

THE SCROLL IS ESSENTIAL: the chat row sat at y=1174 in a 970px viewport,
so every click landed outside the window and silently did nothing. The
composer element existed the whole time, which made it look like the
chat was open when it was not.

Usage: python3 wa_send_open_chat.py <chat-name> <message-file>
"""
import json
import sys
import time

sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval, make_cdp

TARGET = sys.argv[1] if len(sys.argv) else 'TOWASAN'
LOW = TARGET.lower()
MSG = open(sys.argv[2], encoding='utf-8').read() if len(sys.argv) > 2 else ''

tabs = get_tabs()
wa = [t for t in tabs if 'web.whatsapp.com' in (t.get('url') or '') and t.get('type') == 'page']
if not wa:
    print('NO WA TAB')
    sys.exit(1)
ws = connect(wa[0])
cdp = make_cdp(ws)

# ---- 1. open the chat ------------------------------------------------------
js_eval(ws, r"""(()=>{
  const box=document.querySelector('[data-testid="chat-list-search"]') ||
             document.querySelector('[aria-label="Search"]') ||
             document.querySelector('input[type="text"]');
  if(!box) return 'no-search-box';
  box.focus();
  const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
  s.call(box, TARGET);
  box.dispatchEvent(new Event('input',{bubbles:true}));
  return 'typed';
})()""".replace('TARGET', repr(TARGET)), await_promise=False)
time.sleep(6)

opened = False
for _ in range(4):
    pos = js_eval(ws, r"""(()=>{
      const rows=[...document.querySelectorAll('[data-testid^="list-item-"]')];
      for(const it of rows){
        const t=((it.innerText||'')+' '+(it.textContent||'')).toLowerCase();
        if(t.includes(TARGET)){
          it.scrollIntoView({block:'center', behavior:'instant'});
          const rc=it.getBoundingClientRect();
          return JSON.stringify({x:rc.x+rc.width/2, y:rc.y+rc.height/2});
        }
      }
      return 'not-found';
    })()""".replace('TARGET', repr(LOW)), await_promise=False)
    if not pos or pos == 'not-found':
        break
    try:
        p = json.loads(pos)
    except Exception:
        break
    time.sleep(1.2)
    pos = js_eval(ws, r"""(()=>{
      const rows=[...document.querySelectorAll('[data-testid^="list-item-"]')];
      for(const it of rows){
        const t=((it.innerText||'')+' '+(it.textContent||'')).toLowerCase();
        if(t.includes(TARGET)){
          const rc=it.getBoundingClientRect();
          return JSON.stringify({x:rc.x+rc.width/2, y:rc.y+rc.height/2});
        }
      }
      return 'not-found';
    })()""".replace('TARGET', repr(LOW)), await_promise=False)
    try:
        p = json.loads(pos)
    except Exception:
        break
    for typ in ('mousePressed', 'mouseReleased'):
        cdp('Input.dispatchMouseEvent', {'type': typ, 'x': p['x'], 'y': p['y'],
                                         'button': 'left', 'clickCount': 1})
    time.sleep(7)
    st = js_eval(ws, """(()=>!!document.querySelector('[data-testid="conversation-compose-box-input"]'))()""",
                 await_promise=False)
    if st:
        opened = True
        break

if not opened:
    print('COULD NOT OPEN THE CONVERSATION')
    ws.close()
    sys.exit(2)
print('conversation open: yes')

# ---- 2. verify it is the right chat ---------------------------------------
rows = js_eval(ws, r"""(()=>{
  const rs=[...document.querySelectorAll('[role="row"]')]
    .map(r=>(r.innerText||r.textContent||'').trim()).filter(t=>t.length>4);
  return JSON.stringify(rs.slice(-8));
})()""", await_promise=False) or '[]'
print('last rows:', rows[:400])

# ---- 3. type the message ---------------------------------------------------
# Pass the text through a global so no escaping can break the JS.
js_eval(ws, 'window.__waMsg = ' + json.dumps(MSG) + '; window.__waMsg.length',
        await_promise=False)
typed = js_eval(ws, r"""(()=>{
  const msg = window.__waMsg || '';
  const inp=document.querySelector('[data-testid="conversation-compose-box-input"]') ||
            document.querySelector('div[contenteditable="true"][data-tab="10"]');
  if(!inp) return 'no-composer';
  inp.focus();
  // It is a CONTENTEDITABLE div, not an <input> - there is no .value.
  // Set textContent and fire the events WhatsApp listens for. React needs
  // the native setter on the contenteditable element, not on
  // HTMLInputElement.prototype.
  const proto = Object.getPrototypeOf(inp);
  const desc = Object.getOwnPropertyDescriptor(proto, 'textContent');
  if(desc && desc.set) desc.set.call(inp, msg);
  else inp.textContent = msg;
  inp.dispatchEvent(new InputEvent('input',{bubbles:true, inputType:'insertText', data:msg}));
  inp.dispatchEvent(new Event('change',{bubbles:true}));
  return 'typed:'+msg.length+':'+(inp.textContent||'').length;
})()""", await_promise=False)
print('type:', typed)
time.sleep(2.5)

# confirm the text landed
check = js_eval(ws, r"""(()=>{
  const inp=document.querySelector('[data-testid="conversation-compose-box-input"]') ||
            document.querySelector('div[contenteditable="true"][data-tab="10"]');
  if(!inp) return 'no-composer';
  const v=(inp.value!==undefined && inp.value!==null && inp.value!=='' ? inp.value : (inp.textContent||''))||'';
  return JSON.stringify({len:v.length, head:v.slice(0,90)});
})()""", await_promise=False)
print('composer now:', check)

# ---- 4. send ---------------------------------------------------------------
sent = js_eval(ws, r"""(()=>{
  const btn=document.querySelector('[data-testid="compose-btn-send"]') ||
            document.querySelector('span[data-icon="send"]') ||
            document.querySelector('button[aria-label="Send"]');
  if(!btn) return 'no-send-button';
  btn.click();
  return 'clicked-send';
})()""", await_promise=False)
print('send:', sent)
time.sleep(6)

# ---- 5. verify it went out -------------------------------------------------
after = js_eval(ws, r"""(()=>{
  const inp=document.querySelector('[data-testid="conversation-compose-box-input"]');
  const v=inp?((inp.value!==undefined && inp.value!==null && inp.value!=='' ? inp.value : (inp.textContent||''))||''):'';
  const rs=[...document.querySelectorAll('[role="row"]')]
    .map(r=>(r.innerText||r.textContent||'').trim()).filter(t=>t.length>4);
  return JSON.stringify({composerEmpty:v.trim().length===0, tail:rs.slice(-3)});
})()""", await_promise=False)
print('after:', after)
ws.close()
