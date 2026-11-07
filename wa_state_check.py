import sys, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval

tabs = get_tabs()
wa = [t for t in tabs if 'web.whatsapp.com' in (t.get('url') or '') and t.get('type') == 'page']
print('WA tabs:', len(wa))
if not wa:
    sys.exit(1)
ws = connect(wa[0])
js = """(()=>{
  const qr=document.querySelector('canvas');
  const pane=document.querySelector('#pane-side');
  const body=(document.body?document.body.innerText:'').slice(0,900);
  const scan=body.indexOf('Scan to log in');
  return {qr:!!qr, pane:!!pane, scanIdx:scan, body:body};
})()"""
info = js_eval(ws, js, await_promise=False) or {}
print('canvas present :', info.get('qr'))
print('chat pane      :', info.get('pane'))
print('"Scan to log in":', info.get('scanIdx'))
print('--- body ---')
print(info.get('body'))
ws.close()
