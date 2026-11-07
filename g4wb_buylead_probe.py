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


URL = 'https://www.go4worldbusiness.com/list/latest/buyleads'
tid = cdp('Target.createTarget', {'url': URL})['targetId']
s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
cdp('Page.enable', sid=s)
time.sleep(24)

# Find the buy-lead search/filter and the AJAX endpoint that populates the list
print('=== filters / search on the page ===')
print(ev("""(()=>{
  const out=[];
  document.querySelectorAll('input,select').forEach(e=>{
    if(e.type==='hidden') return;
    out.push(e.tagName+'|'+(e.name||e.id||'')+'|'+(e.getAttribute('placeholder')||'')+'|'+(e.getAttribute('data-path')||e.getAttribute('data-url')||''));
  });
  return out.slice(0,30).join('\\n');
})()""", s))

print()
print('=== list AJAX endpoints in hidden inputs ===')
print(ev("""(()=>[...document.querySelectorAll('input[type=hidden]')].map(e=>e.name+'='+(e.value||'').slice(0,70)).filter(x=>/path|url|route|api/i.test(x)).slice(0,22).join('\\n'))()""", s))
ws.close()
