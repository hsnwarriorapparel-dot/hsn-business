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

# Wait for loading to complete
for i in range(30):
    time.sleep(5)
    js = """(()=>({
      url: window.location.href,
      title: document.title,
      readyState: document.readyState,
      body: document.body ? document.body.innerText.slice(0,200) : 'no body',
      paneSide: !!document.querySelector('#pane-side'),
      main: !!document.querySelector('#main'),
      loading: !!document.querySelector('[data-testid="wa-web-loading-screen"]')
    }))()"""
    info = js_eval(ws, js, await_promise=False)
    print(f'Check {i+1}: pane={info.get("paneSide")}, main={info.get("main")}, loading={info.get("loading")}, body={info.get("body", "")[:80]}')
    if info.get('paneSide') and info.get('main'):
        print('READY!')
        break

ws.close()