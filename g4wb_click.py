import sys, json, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect

URL = sys.argv[1]
WAIT = int(sys.argv[2]) if len(sys.argv) > 2 else 18
CLICK_FILE = sys.argv[3] if len(sys.argv) > 3 else None
AFTER_WAIT = int(sys.argv[4]) if len(sys.argv) > 4 else 8
DUMP_FILE = sys.argv[5] if len(sys.argv) > 5 else None

tabs = get_tabs()
gm = [t for t in tabs if 'mail.google' in t.get('url', '') and t.get('type') == 'page']
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


def ev(expr, sess):
    r = cdp('Runtime.evaluate', {'expression': expr, 'returnByValue': True}, session_id=sess)
    return r.get('result', {}).get('value')


tid = cdp('Target.createTarget', {'url': URL})['targetId']
sess = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
cdp('Page.enable', session_id=sess)
time.sleep(WAIT)
if CLICK_FILE:
    print('click:', ev(open(CLICK_FILE, encoding='utf-8').read(), sess))
    time.sleep(AFTER_WAIT)
dump_expr = open(DUMP_FILE, encoding='utf-8').read() if DUMP_FILE else 'JSON.stringify({url:location.href,title:document.title,txt:(document.body?document.body.innerText:"")})'
val = ev(dump_expr, sess)
try:
    print(json.dumps(json.loads(val), indent=1, ensure_ascii=False))
except Exception:
    print(val)
ws.close()
