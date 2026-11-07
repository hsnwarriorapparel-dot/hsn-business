import sys, json, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect

TERMS = sys.argv[1:] or ['martial arts uniform', 'boxing gloves', 'sportswear', 'karate gi', 'taekwondo']

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


for term in TERMS:
    URL = 'https://www.go4worldbusiness.com/list/latest/buyleads?keyword=' + term.replace(' ', '+')
    tid = cdp('Target.createTarget', {'url': URL})['targetId']
    s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
    cdp('Page.enable', sid=s)
    time.sleep(20)
    res = ev("""(()=>{
      const t=document.body?document.body.innerText:'';
      // each buy lead card starts with 'Wanted :'
      const parts=t.split(/Wanted\\s*:/).slice(1);
      const out=parts.map(p=>{
        const head=p.split('\\n').slice(0,3).join(' | ').trim();
        const q=(p.match(/Quantity Required:\\s*([^\\n]+)/)||[])[1]||'';
        const fr=(p.match(/Looking for suppliers from:\\s*([^\\n]+)/)||[])[1]||'';
        const bf=(p.match(/Buyer From\\s*([^\\n]+)/)||[])[1]||'';
        return head.slice(0,120)+' :: Q='+q.slice(0,30)+' :: from='+fr.slice(0,22)+' :: buyer='+bf.slice(0,28);
      });
      return JSON.stringify({count:parts.length, items:out.slice(0,12)});
    })()""", s)
    print('=== %s ===' % term)
    try:
        d = json.loads(res)
        print('  count:', d.get('count'))
        for it in d.get('items') or []:
            print('   >', it)
    except Exception:
        print(' ', str(res)[:300])
    try:
        cdp('Target.closeTarget', {'targetId': tid}, s)
    except Exception:
        pass
ws.close()
