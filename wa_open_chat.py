"""Open a WhatsApp conversation by clicking its title span.

The chat-list ROW click does not open the conversation on the current
WhatsApp Web build - only the pane-side list renders. Clicking the
span[title] that holds the chat name is what actually opens it.
"""
import sys
import time

sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval

TARGET = (sys.argv[1] if len(sys.argv) else 'TOWASAN').lower()

tabs = get_tabs()
wa = [t for t in tabs if 'web.whatsapp.com' in (t.get('url') or '') and t.get('type') == 'page']
if not wa:
    print('NO WA TAB')
    sys.exit(1)
ws = connect(wa[0])

# 1) find the span[title] for the target chat and click it
CLICK = """(()=>{
  const spans=[...document.querySelectorAll('span[title]')];
  const hit=spans.find(s=>(s.getAttribute('title')||'').toLowerCase().includes(TARGET));
  if(!hit) return 'no-title-span';
  hit.click();
  return 'clicked:'+(hit.getAttribute('title')||'');
})()""".replace('TARGET', repr(TARGET))
print('click:', js_eval(ws, CLICK, await_promise=False))
time.sleep(10)

# 2) read the conversation pane
DUMP = r"""(()=>{
  const out={};
  // the conversation pane sits next to pane-side
  const grids=[...document.querySelectorAll('[role="grid"]')];
  out.grids=grids.map((g,i)=>({i, rows:g.querySelectorAll('[role="row"]').length,
                               text:(g.innerText||'').slice(0,3000)}));
  // header = the chat title at the top of the conversation
  const hdr=document.querySelector('header span[title]');
  out.header = hdr?hdr.getAttribute('title'):null;
  // the message list container
  const panes=[...document.querySelectorAll('div[id]')].filter(d=>/pane|chat/i.test(d.id));
  out.paneIds=panes.map(d=>({id:d.id, len:(d.innerText||'').length}));
  return JSON.stringify(out);
})()"""
res = js_eval(ws, DUMP, await_promise=False)
print()
print(res)
ws.close()
