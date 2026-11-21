import sys, json, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval

tabs = get_tabs()
wa = [t for t in tabs if 'web.whatsapp.com' in (t.get('url') or '') and t.get('type') == 'page']
if not wa:
    print('NO WA TAB')
    sys.exit(1)
ws = connect(wa[0])

# Check page state after click
js = """(()=>({
  url: window.location.href,
  title: document.title,
  main: !!document.querySelector('#main'),
  composer: !!document.querySelector('[data-testid="conversation-compose-box-input"]'),
  composer2: !!document.querySelector('div[contenteditable="true"][data-tab="10"]'),
  allComposers: [...document.querySelectorAll('[contenteditable="true"]')].map(e=>({tag: e.tagName, testid: e.getAttribute("data-testid"), tab: e.getAttribute("data-tab"), aria: e.getAttribute("aria-label"), class: e.className.slice(0,50)})).filter(e=>e.testid||e.tab||e.aria),
  selectedChat: document.querySelector('[aria-selected="true"]') ? 'yes' : 'no'
}))()"""
info = js_eval(ws, js, await_promise=False)
print(json.dumps(info, indent=2))

ws.close()