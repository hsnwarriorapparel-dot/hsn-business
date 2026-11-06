import sys, time, json
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval

QUERY = sys.argv[1] if len(sys.argv) > 1 else 'alvarocampeao'

tabs = get_tabs()
gm = [t for t in tabs if 'mail.google' in t.get('url', '') and t.get('type') == 'page']
if not gm:
    print('NO GMAIL TAB'); sys.exit(1)
ws = connect(gm[0])
js = """(()=>{const box=document.querySelector('input[aria-label="Search mail"]')||document.querySelector('input[name="q"]');if(!box)return 'no-box';box.focus();const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;s.call(box,QUERY);box.dispatchEvent(new Event('input',{bubbles:true}));for(const t of ['keydown','keypress','keyup'])box.dispatchEvent(new KeyboardEvent(t,{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}));return 'typed';})()""".replace('QUERY', json.dumps(QUERY))
js_eval(ws, js, await_promise=False)
time.sleep(12)
# click the first conversation to open it
opened = js_eval(ws, """(()=>{const rows=[...document.querySelectorAll('div[role="listitem"]')];if(rows.length){rows[0].click();return 'clicked-listitem:'+rows.length;}const sp=[...document.querySelectorAll('span')].filter(s=>/Custom martial arts gear|RE:|Alvaro/i.test(s.textContent||''));if(!sp.length)return 'no-rows';sp[sp.length-1].click();return 'clicked-span:'+sp.length;})()""", await_promise=False)
print('open:', opened)
time.sleep(9)
txt = js_eval(ws, """(()=>{const m=document.querySelector('div[role="main"]');return m?m.innerText:'';})()""", await_promise=False) or ''
ws.close()
print('---- CONVERSATION ----')
print(txt[:6000])
