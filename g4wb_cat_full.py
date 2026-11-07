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
        return 'JS_ERR: ' + str(r['exceptionDetails'])[:200]
    return r.get('result', {}).get('value')


URL = 'https://www.go4worldbusiness.com/member/dashboard/company-profile'
tid = cdp('Target.createTarget', {'url': URL})['targetId']
s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
cdp('Page.enable', sid=s)
time.sleep(23)

# 1. get the whole category tree (empty search may return the root list)
print('=== full category list (empty search) ===')
out = ev("""(async()=>{
  const r=await fetch('/signup/ajax/category-search?q=',{headers:{'X-Requested-With':'XMLHttpRequest'}});
  const t=await r.text();
  return 'status='+r.status+' len='+t.length+' :: '+t.slice(0,1500);
})()""", s)
print(out)

# 2. what does the selection-save endpoint expect?
print()
print('=== try category-selection GET (probe params) ===')
print(ev("""(async()=>{
  const urls=['/signup/ajax/category-selection','/signup/ajax/category-selection?ids=1211900992'];
  const out=[];
  for(const u of urls){
    try{const r=await fetch(u,{headers:{'X-Requested-With':'XMLHttpRequest'}});const t=await r.text();out.push(u+' -> '+r.status+' len='+t.length+' :: '+t.slice(0,200));}catch(e){out.push(u+' ERR '+e);}
  }
  return out.join('\\n');
})()""", s))
ws.close()
