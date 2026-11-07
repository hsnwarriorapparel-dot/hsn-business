import sys, json, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect

SITES = ['https://www.cssportinggoods.com', 'https://eu.venum.com']

tabs = get_tabs()
gm = [t for t in tabs if 'mail.google' in (t.get('url') or '') and t.get('type') == 'page']
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
        return 'JS_ERR: ' + str(r['exceptionDetails'])[:200]
    return r.get('result', {}).get('value')


for url in SITES:
    tid = cdp('Target.createTarget', {'url': url})['targetId']
    s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
    cdp('Page.enable', sid=s)
    time.sleep(11)
    print('=' * 72)
    print(url)
    print('TITLE:', ev('document.title', s))
    print('TEXT :', (ev("(document.body?document.body.innerText:'').replace(/\\s+/g,' ').slice(0,600)", s) or '')[:600])
    print('EMAILS:', ev("""JSON.stringify([...new Set([...document.body.innerText.matchAll(/[\\w.+-]+@[\\w.-]+\\.\\w{2,}/g)].map(m=>m[0]))].slice(0,6))""", s))
    print('PRODUCT WORDS:', ev("""JSON.stringify(['boxing','glove','martial','karate','sports','uniform','apparel','training','fitness'].filter(w=>(document.body?document.body.innerText:'').toLowerCase().includes(w)))""", s))
    try:
        cdp('Target.closeTarget', {'targetId': tid})
    except Exception:
        pass
ws.close()
