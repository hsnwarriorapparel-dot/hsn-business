"""Open a URL in a NEW work-browser tab and read it, without disturbing the
Gmail / Instagram / WhatsApp tabs.

Uses raw CDP over the browser-level websocket with a flattened session, which
is the channel that never wedges (per refs/browser-tab-recovery.md).

Usage: g4wb_read.py <url> [wait_seconds]
"""
import sys, json, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect
import websocket  # websocket-client

URL = sys.argv[1] if len(sys.argv) > 1 else 'https://www.go4worldbusiness.com/member/dashboard/'
WAIT = int(sys.argv[2]) if len(sys.argv) > 2 else 18
EXPR = sys.argv[3] if len(sys.argv) > 3 else 'JSON.stringify({url:location.href,title:document.title,txt:(document.body?document.body.innerText:"")})'

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
        raw = ws.recv()
        data = json.loads(raw)
        if data.get('id') == mid:
            if 'error' in data:
                raise RuntimeError(data['error'])
            return data.get('result', {})
        # ignore events
    raise TimeoutError(method)


cdp('Target.createTarget', {'url': 'about:blank'})
tids = cdp('Target.getTargets')['targetInfos']
tid = None
for t in tids:
    if t.get('type') == 'page' and 'go4worldbusiness' not in t.get('url', ''):
        pass
# create the real target
res = cdp('Target.createTarget', {'url': URL})
tid = res['targetId']
print('target:', tid)
sess = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
cdp('Page.enable', session_id=sess)
time.sleep(WAIT)
r = cdp('Runtime.evaluate', {'expression': EXPR, 'returnByValue': True}, session_id=sess)
val = r.get('result', {}).get('value')
try:
    print(json.dumps(json.loads(val), indent=1, ensure_ascii=False))
except Exception:
    print(val)
ws.close()
