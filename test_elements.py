import sys, json, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval

tabs = get_tabs()
wa = [t for t in tabs if 'web.whatsapp.com' in (t.get('url') or '') and t.get('type') == 'page']
if not wa:
    print('NO WA TAB')
    sys.exit(1)
ws = connect(wa[0])

# Go back to main WhatsApp Web
import urllib.request, websocket
ws2 = websocket.create_connection(
    json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/version"))["webSocketDebuggerUrl"],
    timeout=30, suppress_origin=True)
def cdp_call(method, params=None):
    import json as _json
    cdp_id = [0]
    def _call(m, p):
        cdp_id[0] += 1
        ws2.send(_json.dumps({"id": cdp_id[0], "method": m, "params": p or {}}))
        while True:
            msg = _json.loads(ws2.recv())
            if msg.get("id") == cdp_id[0]:
                if "error" in msg:
                    raise RuntimeError(f"CDP error: {msg['error']}")
                return msg.get("result", {})
    return _call(method, params)

cdp_call('Page.navigate', {'url': 'https://web.whatsapp.com/'})
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
for b in info.get('buttons', [])[:20]:
    print(f'  {b}')
print('\nInputs:')
for i in info.get('inputs', [])[:20]:
    print(f'  {i}')

ws.close()
ws2.close()