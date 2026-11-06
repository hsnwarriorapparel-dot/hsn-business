import sys, time, json
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval

QUERY = sys.argv[1] if len(sys.argv) > 1 else 'in:spam newer_than:7d'

tabs = get_tabs()
gm = [t for t in tabs if 'mail.google' in t.get('url', '') and t.get('type') == 'page']
if not gm:
    print('NO GMAIL TAB')
    sys.exit(1)
ws = connect(gm[0])
js = """(()=>{const box=document.querySelector('input[aria-label="Search mail"]')||document.querySelector('input[name="q"]');if(!box)return 'no-box';box.focus();const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;s.call(box,QUERY);box.dispatchEvent(new Event('input',{bubbles:true}));for(const t of ['keydown','keypress','keyup'])box.dispatchEvent(new KeyboardEvent(t,{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}));return 'typed';})()""".replace('QUERY', json.dumps(QUERY))
print('typed:', js_eval(ws, js, await_promise=False))
time.sleep(12)
txt = js_eval(ws, """(()=>{const m=document.querySelector('div[role="main"]');return m?m.innerText:'';})()""", await_promise=False) or ''
ws.close()
lines = [l.strip() for l in txt.splitlines() if l.strip() and len(l.strip()) > 6]
print('QUERY:', QUERY)
print('rows:', len(lines))
for l in lines[:18]:
    print('  >', l[:150])
