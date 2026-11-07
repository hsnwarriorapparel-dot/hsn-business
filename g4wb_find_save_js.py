import sys, json, time
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


URL = 'https://www.go4worldbusiness.com/member/dashboard/company-profile'
tid = cdp('Target.createTarget', {'url': URL})['targetId']
s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
cdp('Page.enable', sid=s)
time.sleep(23)

# Look at the site's own JS to find how the selection is saved.
print('=== search inline scripts for category-selection usage ===')
print(ev("""(()=>{
  const scripts=[...document.querySelectorAll('script')].map(s=>s.textContent||'').join('\\n');
  const out=[];
  const re=/category-selection[^]{0,300}/g;
  let m;while((m=re.exec(scripts))&&out.length<5)out.push(m[0].replace(/\\s+/g,' '));
  const re2=/category-search[^]{0,200}/g;
  while((m=re2.exec(scripts))&&out.length<8)out.push(m[0].replace(/\\s+/g,' '));
  return out.join('\\n---\\n')||'none-inline';
})()""", s))

print()
print('=== external JS files ===')
print(ev("""(()=>[...document.querySelectorAll('script[src]')].map(s=>s.getAttribute('src')).slice(0,14).join('\\n'))()""", s))
ws.close()
