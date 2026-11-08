"""Open a WhatsApp chat with a REAL mouse event at the row's coordinates.

A JS .click() on the chat row registers but WhatsApp Web ignores it - the
conversation pane stays empty. A CDP Input.dispatchMouseEvent at the
element's box centre is what actually opens it.
"""
import sys
import time
import json

sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval, make_cdp

TARGET = sys.argv[1] if len(sys.argv) else 'TOWASAN'
LOW = TARGET.lower()

tabs = get_tabs()
wa = [t for t in tabs if 'web.whatsapp.com' in (t.get('url') or '') and t.get('type') == 'page']
if not wa:
    print('NO WA TAB')
    sys.exit(1)
ws = connect(wa[0])
cdp = make_cdp(ws)


def search():
    return js_eval(ws, r"""(()=>{
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


def find_row():
    # SCROLL IT INTO VIEW FIRST. The chat row was at y=1174 with a ~900px
    # viewport, so every click landed outside the window and did nothing.
    return js_eval(ws, r"""(()=>{
      const rows=[...document.querySelectorAll('[data-testid^="list-item-"]')];
      for(const it of rows){
        const t=((it.innerText||'')+' '+(it.textContent||'')).toLowerCase();
        if(t.includes(TARGET)){
          it.scrollIntoView({block:'center', behavior:'instant'});
          const rc=it.getBoundingClientRect();
          return JSON.stringify({x:rc.x+rc.width/2, y:rc.y+rc.height/2,
                                 w:rc.width, h:rc.height, id:it.getAttribute('data-testid'),
                                 vh:window.innerHeight});
        }
      }
      return 'not-found';
    })()""".replace('TARGET', repr(LOW)), await_promise=False)


def pane_state():
    return js_eval(ws, r"""(()=>{
      const out={};
      out.composer=!!document.querySelector('[data-testid="conversation-compose-box-input"]');
      const hdr=document.querySelector('header span[title]');
      out.header=hdr?hdr.getAttribute('title'):null;
      const dr=document.querySelector('div[data-testid="drawer-right"]');
      out.paneLen=dr?(dr.innerText||'').length:0;
      out.paneText=dr?(dr.innerText||'').slice(0,2500):'';
      return JSON.stringify(out);
    })()""", await_promise=False)


print('search:', search())
time.sleep(6)

for attempt in range(4):
    pos = find_row()
    print('attempt %d row: %s' % (attempt, pos))
    if not pos or pos == 'not-found':
        break
    try:
        p = json.loads(pos)
    except Exception:
        break
    time.sleep(1.5)
    pos = find_row()
    try:
        p = json.loads(pos)
    except Exception:
        break
    for typ in ('mousePressed', 'mouseReleased'):
        cdp('Input.dispatchMouseEvent', {'type': typ, 'x': p['x'], 'y': p['y'],
                                         'button': 'left', 'clickCount': 1})
    time.sleep(8)
    st = pane_state()
    print('  pane:', st[:220])
    try:
        if json.loads(st).get('composer'):
            print('  CONVERSATION OPEN')
            break
    except Exception:
        pass
    # if still closed, try clicking the title span inside the row
    ts = js_eval(ws, r"""(()=>{
      const rows=[...document.querySelectorAll('[data-testid^="list-item-"]')];
      for(const it of rows){
        const t=((it.innerText||'')+' '+(it.textContent||'')).toLowerCase();
        if(t.includes(TARGET)){
          const sp=it.querySelector('span[title]');
          if(sp){ sp.scrollIntoView({block:'center', behavior:'instant'});
            const rc=sp.getBoundingClientRect();
            return JSON.stringify({x:rc.x+rc.width/2,y:rc.y+rc.height/2,title:sp.getAttribute('title')}); }
        }
      }
      return 'no-span';
    })()""".replace('TARGET', repr(LOW)), await_promise=False)
    print('  title span:', ts)
    if ts and ts != 'no-span':
        try:
            q = json.loads(ts)
            for typ in ('mousePressed', 'mouseReleased'):
                cdp('Input.dispatchMouseEvent', {'type': typ, 'x': q['x'], 'y': q['y'],
                                                 'button': 'left', 'clickCount': 1})
            time.sleep(8)
            st2 = pane_state()
            print('  pane after title click:', st2[:220])
            try:
                if json.loads(st2).get('composer'):
                    print('  CONVERSATION OPEN (via title)')
                    break
            except Exception:
                pass
        except Exception:
            pass

print()
print('FINAL:', pane_state()[:2500])
ws.close()
