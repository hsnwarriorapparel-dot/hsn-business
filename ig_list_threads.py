import sys, time, json
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval

tabs = get_tabs()
ig = [t for t in tabs if 'instagram.com' in t.get('url', '') and t.get('type') == 'page']
if not ig:
    print('NO IG TAB'); sys.exit(1)
ws = connect(ig[0])
js_eval(ws, "(()=>{const b=document.querySelector('a[href=\"/direct/inbox/\"]')||document.querySelector('a[href*=\"direct\"]');if(b){b.click();return 'clicked-inbox';}return 'no-inbox-link';})()", await_promise=False)
time.sleep(8)
# read the thread list
threads = js_eval(ws, """(()=>{
  const out=[];
  const els=[...document.querySelectorAll('a[href^="/direct/t/"]')];
  const seen=new Set();
  for(const e of els){
    const t=(e.textContent||'').trim().replace(/\\s+/g,' ');
    const k=e.getAttribute('href')+'|'+t.slice(0,40);
    if(seen.has(k))continue; seen.add(k);
    out.push({href:e.getAttribute('href'), text:t.slice(0,120)});
  }
  return out;
})()""", await_promise=False) or []
print('threads found:', len(threads))
for t in threads[:25]:
    print('  ', t.get('href'), '|', t.get('text'))
ws.close()
