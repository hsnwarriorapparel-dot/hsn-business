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

# Go back to main WhatsApp Web
cdp('Page.navigate', {'url': 'https://web.whatsapp.com/'})
time.sleep(5)

# Click new chat button
js = """(()=>{
  const btn = document.querySelector('[data-testid="new-chat-button"]') ||
              document.querySelector('[aria-label="New chat"]') ||
              document.querySelector('[title="New chat"]');
  if(btn) { btn.click(); return 'clicked'; }
  return 'not-found';
})()"""
result = js_eval(ws, js, await_promise=False)
print('New chat button:', result)

time.sleep(2)

# Type phone number in search
phone = "34661571463"
js = f"""(()=>{{
  const box = document.querySelector('[data-testid="chat-list-search"]') ||
              document.querySelector('[aria-label="Search"]') ||
              document.querySelector('input[type="text"]');
  if(!box) return 'no-search-box';
  box.focus();
  const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
  s.call(box, {json.dumps(phone)});
  box.dispatchEvent(new Event('input',{{bubbles:true}}));
  return 'typed';
}})()"""
result = js_eval(ws, js, await_promise=False)
print('Search typed:', result)

time.sleep(3)

# Check results
js = """(()=>{
  const rows=[...document.querySelectorAll('[data-testid^="list-item-"]')];
  return JSON.stringify(rows.map(it=>((it.innerText||'')+' '+(it.textContent||'')).replace(/\\n/g,' | ').slice(0,200)).filter(Boolean));
})()"""
results = js_eval(ws, js, await_promise=False) or '[]'
results = json.loads(results)
print(f'Search results ({len(results)}):')
for r in results:
    print(f'  {r}')

ws.close()