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
time.sleep(8)

# Check page state
js = """(()=>({
  url: window.location.href,
  title: document.title,
  readyState: document.readyState,
  body: document.body ? document.body.innerText.slice(0,500) : 'no body',
  paneSide: !!document.querySelector('#pane-side'),
  main: !!document.querySelector('#main'),
  allTestIds: [...document.querySelectorAll('[data-testid]')].map(e=>e.getAttribute('data-testid')).slice(0,30)
}))()"""
info = js_eval(ws, js, await_promise=False)
print(json.dumps(info, indent=2))

ws.close()