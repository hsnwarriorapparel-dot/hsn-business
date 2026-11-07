import sys, json, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect

# Read the member's page first to see if it is a BUYER or a supplier, and
# what they are looking for.
HREF = sys.argv[1]
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


URL = 'https://www.go4worldbusiness.com' + HREF
tid = cdp('Target.createTarget', {'url': URL})['targetId']
s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
cdp('Page.enable', sid=s)
time.sleep(24)

out = ev("""(()=>{
  const t = document.body ? document.body.innerText : '';
  const i = t.search(/Buyer Of|Selling|Supplier|Trading|Manufacturer|Sending Inquiry/);
  const o = [];
  o.push('URL: ' + location.href);
  o.push(t.slice(Math.max(0,i-120), i+1400).replace(/\\n+/g,' | '));
  // the company blurb / product categories
  const bl = [...document.querySelectorAll('p,div,span')].map(e=>(e.innerText||'').trim())
    .filter(x=>x.length>40 && x.length<400 && /buyer of|looking for|we buy|we need|interested in|import/i.test(x));
  o.push('BLURBS: ' + [...new Set(bl)].slice(0,4).join(' || '));
  return o.join('\\n---\\n');
})()""", s)
print(out)
ws.close()
