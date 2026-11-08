"""Open a WhatsApp chat via the SEARCH BOX and read the conversation.

The working method (the one wa_sender_cdp.py uses for its 74 successful
sends): type the name into WhatsApp's search box, then click the contact
in the results list. Clicking a row in the chat list does NOT open the
conversation on this build.

Usage: python3 wa_read_via_search.py <name>
"""
import sys
import time

sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval

TARGET = sys.argv[1] if len(sys.argv) else 'TOWASAN'

tabs = get_tabs()
wa = [t for t in tabs if 'web.whatsapp.com' in (t.get('url') or '') and t.get('type') == 'page']
if not wa:
    print('NO WA TAB')
    sys.exit(1)
ws = connect(wa[0])

SEARCH = r"""(()=>{
  const box=document.querySelector('input[type="text"]');
  if(!box) return 'no-search-box';
  box.focus();
  const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
  s.call(box, TARGET);
  box.dispatchEvent(new Event('input',{bubbles:true}));
  return 'typed';
})()""".replace('TARGET', repr(TARGET))
print('search:', js_eval(ws, SEARCH, await_promise=False))
time.sleep(7)

CLICK = r"""(()=>{
  const hits=[...document.querySelectorAll('[role="listitem"],[role="row"],div[data-testid="cell"]')]
    .filter(e=>((e.innerText||'')+' '+(e.textContent||'')).toLowerCase().includes(TARGET.toLowerCase()));
  if(!hits.length) return 'no-result';
  hits[0].click();
  return 'clicked';
})()""".replace('TARGET', repr(TARGET.lower()))
print('click result:', js_eval(ws, CLICK, await_promise=False))
time.sleep(10)

DUMP = r"""(()=>{
  const out={};
  const inp=document.querySelector('[data-testid="conversation-compose-box-input"]');
  out.composerPresent=!!inp;
  const hdr=document.querySelector('header span[title]');
  out.header=hdr?hdr.getAttribute('title'):null;
  // message bubbles live in the conversation pane
  const rows=[...document.querySelectorAll('[role="row"]')];
  const msgs=rows.map(r=>(r.innerText||r.textContent||'').trim()).filter(t=>t.length>2);
  // the chat-list rows come first; keep the tail (the conversation)
  out.total=msgs.length;
  out.tail=msgs.slice(-14);
  return JSON.stringify(out);
})()"""
res = js_eval(ws, DUMP, await_promise=False)
print()
print(res)
ws.close()
