import sys, time, json
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval

QUERY = sys.argv[1] if len(sys.argv) > 1 else 'subject:(Saints and Stars)'
SUBJECT_MATCH = sys.argv[2] if len(sys.argv) > 2 else 'Saints and Stars'

tabs = get_tabs()
gm = [t for t in tabs if 'mail.google' in t.get('url', '') and t.get('type') == 'page']
if not gm:
    print('NO GMAIL TAB'); sys.exit(1)
ws = connect(gm[0])
js = """(()=>{const box=document.querySelector('input[aria-label="Search mail"]')||document.querySelector('input[name="q"]');if(!box)return 'no-box';box.focus();const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;s.call(box,QUERY);box.dispatchEvent(new Event('input',{bubbles:true}));for(const t of ['keydown','keypress','keyup'])box.dispatchEvent(new KeyboardEvent(t,{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}));return 'typed';})()""".replace('QUERY', json.dumps(QUERY))
js_eval(ws, js, await_promise=False)
time.sleep(13)
js_eval(ws, """(()=>{
  const sp=[...document.querySelectorAll('span')].filter(s=>(s.textContent||'').includes(SM));
  if(!sp.length) return 'no';
  sp[sp.length-1].click(); return 'clicked';
})()""".replace('SM', json.dumps(SUBJECT_MATCH)), await_promise=False)
time.sleep(11)

# Expand any clipped messages, then read every message bubble in order
expanded = js_eval(ws, """(()=>{
  const links=[...document.querySelectorAll('span')].filter(s=>/View entire message|View full message|show trimmed/i.test(s.textContent||''));
  links.forEach(l=>{try{l.click();}catch(e){}});
  return links.length;
})()""", await_promise=False)
print('expanded:', expanded)
time.sleep(4)

info = js_eval(ws, """(()=>{
  const out={};
  // each message bubble. 'div.ii.gt' is the classic selector, but Gmail
  // renamed/reshaped the DOM on 2026-11-08, so try several and fall back
  // to a content-based scan for elements that look like a message.
  const sel=['div.ii.gt','div.adn.ads','div.adx.ads','div.ii','div[role=listitem]',
             'div[data-message-id]','div.adn.ads.adx.ads'];
  let msgs=[];
  for(const s of sel){
    const got=[...document.querySelectorAll(s)];
    if(got.length>msgs.length) msgs=got;
  }
  if(!msgs.length){
    const main=document.querySelector('div[role="main"]');
    const all=main?[...main.querySelectorAll('div,tr')]:[];
    const cand=all.filter(el=>{
      const t=(el.innerText||'').trim();
      return t.length>40 && t.length<4000 && el.querySelectorAll('*').length<60 &&
             /(Reply|More|Add reaction)|wrote:|escribi|[0-9]{1,2}:[0-9]{2} ?[AP]M/.test(t);
    });
    msgs=cand.filter(el=>!cand.some(o=>o!==el&&el.contains(o)));
  }
  // Gmail virtualises the thread view too - innerText can be empty while
  // textContent holds the message. Read textContent first.
  out.msgs=msgs.map(m=>((m.textContent||'')+(m.innerText||'')).trim())
                .filter(t=>t.length>3);
  // fallback: the whole thread pane
  const main=document.querySelector('div[role="main"]');
  out.full=(main?main.innerText:'').slice(0,9000);
  return out;
})()""", await_promise=False) or {}
print()
print('==== MESSAGE BUBBLES (' + str(len(info.get('msgs') or [])) + ') ====')
for i, m in enumerate(info.get('msgs') or [], 1):
    print('--- [%d] ---' % i)
    print(m[:1400])
if not info.get('msgs'):
    print('(no bubbles) FULL PANE:')
    print(info.get('full'))
ws.close()
