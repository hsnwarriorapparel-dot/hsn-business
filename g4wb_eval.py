import sys, json, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect

URL = sys.argv[1] if len(sys.argv) > 1 else 'https://www.go4worldbusiness.com/member/dashboard/'
WAIT = int(sys.argv[2]) if len(sys.argv) > 2 else 18
EXPR_FILE = sys.argv[3] if len(sys.argv) > 3 else None

expr = None
if EXPR_FILE:
    expr = open(EXPR_FILE, encoding='utf-8').read()

tabs = get_tabs()
gm = [t for t in tabs if 'mail.google' in t.get('url', '') and t.get('type') == 'page']
if not gm:
    print('NO BROWSER TAB'); sys.exit(1)
ws = connect(gm[0])
_next = [0]


def cdp(method, params=None, session_id=None):
    _next[0] += 1
    mid = _next[0]
    msg = {'id': mid, 'method': method, 'params': params or {}}
    if session_id:
        msg['sessionId'] = session_id
    ws.send(json.dumps(msg))
    deadline = time.time() + 40
    while time.time() < deadline:
        data = json.loads(ws.recv())
        if data.get('id') == mid:
            if 'error' in data:
                raise RuntimeError(data['error'])
            return data.get('result', {})
    raise TimeoutError(method)


tid = cdp('Target.createTarget', {'url': URL})['targetId']
sess = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
cdp('Page.enable', session_id=sess)
time.sleep(WAIT)
if expr is None:
    expr = 'JSON.stringify({url:location.href,title:document.title,txt:(document.body?document.body.innerText:"")})'
r = cdp('Runtime.evaluate', {'expression': expr, 'returnByValue': True}, session_id=sess)
val = r.get('result', {}).get('value')
try:
    print(json.dumps(json.loads(val), indent=1, ensure_ascii=False))
except Exception:
    print(val)
ws.close()
