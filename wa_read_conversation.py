"""Open a WhatsApp chat and read the conversation.

WORKING selectors on the current WhatsApp Web build:
  - chat row:    [data-testid^="list-item-"]  (NOT role=listitem)
  - title span:  span[title]
  - composer:    [data-testid="conversation-compose-box-input"]

Clicking a role="listitem" does nothing on this build - the rows carry
data-testid="list-item-N" instead.

Usage: python3 wa_read_conversation.py <name>
"""
import sys
import time

sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval

TARGET = sys.argv[1] if len(sys.argv) else 'TOWASAN'
LOW = TARGET.lower()

tabs = get_tabs()
wa = [t for t in tabs if 'web.whatsapp.com' in (t.get('url') or '') and t.get('type') == 'page']
if not wa:
    print('NO WA TAB')
    sys.exit(1)
ws = connect(wa[0])

SEARCH = r"""(()=>{
  const box=document.querySelector('[data-testid="chat-list-search"]') ||
             document.querySelector('[aria-label="Search"]') ||
             document.querySelector('input[type="text"]');
  if(!box) return 'no-search-box';
  box.focus();
  const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
  s.call(box, TARGET);
  box.dispatchEvent(new Event('input',{bubbles:true}));
  return 'typed';
})()""".replace('TARGET', repr(TARGET))
print('search:', js_eval(ws, SEARCH, await_promise=False))
time.sleep(6)

CLICK = r"""(()=>{
  const rows=[...document.querySelectorAll('[data-testid^="list-item-"]')];
  for(const it of rows){
    const t=((it.innerText||'')+' '+(it.textContent||'')).toLowerCase();
    if(t.includes(TARGET)){
      it.click();
      return 'clicked:'+it.getAttribute('data-testid');
    }
  }
  if(rows.length){ rows[0].click(); return 'clicked-first:'+rows[0].getAttribute('data-testid'); }
  return 'no-rows';
})()""".replace('TARGET', repr(LOW))
print('click:', js_eval(ws, CLICK, await_promise=False))
time.sleep(10)

DUMP = r"""(()=>{
  const out={};
  out.composerPresent=!!document.querySelector('[data-testid="conversation-compose-box-input"]');
  const hdr=document.querySelector('header span[title]');
  out.header=hdr?hdr.getAttribute('title'):null;
  // the conversation pane is #pane-side's sibling; grab it by the composer
  let pane=null;
  const comp=document.querySelector('[data-testid="conversation-compose-box-input"]');
  if(comp){
    let e=comp;
    for(let i=0;i<8 && e;i++){ e=e.parentElement; if(e && e.id==='pane-side') break; }
    pane=e;
  }
  if(!pane) pane=document.querySelector('div[data-testid="drawer-right"]');
  if(pane){
    const rows=[...pane.querySelectorAll('[role="row"]')].map(r=>(r.innerText||r.textContent||'').trim()).filter(Boolean);
    out.rows=rows.slice(-16);
    if(!rows.length) out.paneText=(pane.innerText||'').slice(0,3000);
  }
  return JSON.stringify(out);
})()"""
res = js_eval(ws, DUMP, await_promise=False)
print()
print(res)
ws.close()
