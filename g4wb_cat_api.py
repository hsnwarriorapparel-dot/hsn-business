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

# Try the category search AJAX from inside the page (same-origin, carries cookies)
for term in ('sportswear', 'uniform', 'martial'):
    js = """(async()=>{
      const url='/signup/ajax/category-search';
      try{
        const body=new URLSearchParams();
        body.append('search',TERM);
        body.append('q',TERM);
        const q='?search='+encodeURIComponent(TERM)+'&q='+encodeURIComponent(TERM);
        let r=await fetch(url+q,{headers:{'X-Requested-With':'XMLHttpRequest'}});
        if(r.status>=400){ r=await fetch(url+q,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded','X-Requested-With':'XMLHttpRequest'},body:body.toString()}); }
        const t=await r.text();
        return 'status='+r.status+' len='+t.length+' :: '+t.slice(0,700);
      }catch(e){return 'ERR '+e;}
    })()""".replace('TERM', json.dumps(term))
    print('--- search:', term)
    print(ev(js, s))
    print()
ws.close()
