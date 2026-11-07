import sys, json, time, base64
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect

tabs = get_tabs()
gm = [t for t in tabs if 'mail.google' in t.get('url', '') and t.get('type') == 'page']
if not gm:
    print('NO BROWSER TAB'); sys.exit(1)
ws = connect(gm[0]); _n = [0]


def cdp(m, p=None, sid=None):
    _n[0] += 1; mid = _n[0]
    msg = {'id': mid, 'method': m, 'params': p or {}}
    if sid: msg['sessionId'] = sid
    ws.send(json.dumps(msg))
    t = time.time() + 50
    while time.time() < t:
        d = json.loads(ws.recv())
        if d.get('id') == mid:
            if 'error' in d: raise RuntimeError(d['error'])
            return d.get('result', {})
    raise TimeoutError(m)


def ev(e, s):
    r = cdp('Runtime.evaluate', {'expression': e, 'returnByValue': True, 'awaitPromise': True}, sid=s)
    if r.get('exceptionDetails'):
        return 'JS_ERR: ' + str(r['exceptionDetails'])[:250]
    return r.get('result', {}).get('value')


URL = sys.argv[1] if len(sys.argv) > 1 else 'https://www.go4worldbusiness.com/inquiries/send/buyleads/1333286/wanted-:-soccer-football-jerseys-unit-units'
OUT = sys.argv[2] if len(sys.argv) > 2 else '/home/ubuntu/g4wb_captcha.png'

tid = cdp('Target.createTarget', {'url': URL})['targetId']
s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
cdp('Page.enable', sid=s)
time.sleep(24)

# Screenshot the captcha image element via CDP
box = ev("""(()=>{
  const i=document.querySelector('#form_captcha_image');
  if(!i) return null;
  const r=i.getBoundingClientRect();
  return JSON.stringify({x:r.x,y:r.y,w:r.width,h:r.height});
})()""", s)
print('box:', box)
if not box:
    print('NO CAPTCHA IMAGE'); ws.close(); sys.exit(1)
b = json.loads(box)
r = cdp('Page.captureScreenshot', {
    'format': 'png',
    'clip': {'x': b['x'], 'y': b['y'], 'width': b['w'], 'height': b['h'], 'scale': 3},
}, s)
data = r.get('data')
if data:
    open(OUT, 'wb').write(base64.b64decode(data))
    print('saved ->', OUT)
ws.close()
