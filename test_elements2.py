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

# Find all buttons and inputs
js = """(()=>{
  const btns = [...document.querySelectorAll('button, [role="button"]')];
  const inputs = [...document.querySelectorAll('input, [contenteditable="true"]')];
  return JSON.stringify({
    buttons: btns.map(b=>({text: (b.innerText||b.textContent||'').slice(0,50), aria: b.getAttribute('aria-label')||'', testid: b.getAttribute('data-testid')||'', class: b.className.slice(0,50)})).filter(b=>b.text||b.aria||b.testid),
    inputs: inputs.map(i=>({text: (i.innerText||i.textContent||'').slice(0,50), aria: i.getAttribute('aria-label')||'', testid: i.getAttribute('data-testid')||'', type: i.type||'', class: i.className.slice(0,50)})).filter(i=>i.text||i.aria||i.testid||i.type)
  });
})()"""
info = js_eval(ws, js, await_promise=False) or '{}'
info = json.loads(info)
print('Buttons:')
for b in info.get('buttons', [])[:30]:
    print(f'  {b}')
print('\nInputs:')
for i in info.get('inputs', [])[:30]:
    print(f'  {i}')

ws.close()