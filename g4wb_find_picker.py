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
    r = cdp('Runtime.evaluate', {'expression': e, 'returnByValue': True}, sid=s)
    return r.get('result', {}).get('value')


URL = sys.argv[1] if len(sys.argv) > 1 else 'https://www.go4worldbusiness.com/member/dashboard/company-profile'
tid = cdp('Target.createTarget', {'url': URL})['targetId']
s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
cdp('Page.enable', sid=s)
time.sleep(23)

JS = r"""(()=>{
  const hits=[];
  document.querySelectorAll('*').forEach(e=>{
    const cls=(e.className||'').toString();
    const id=e.id||'';
    const da=JSON.stringify(e.dataset||{});
    if(/categor|industr|dealsin|tags-editor|product.?group/i.test(cls+' '+id+' '+da)){
      hits.push(e.tagName+' | cls='+cls.slice(0,44)+' | id='+id.slice(0,30)+' | data='+da.slice(0,70)+' | txt='+(e.textContent||'').trim().replace(/\s+/g,' ').slice(0,80));
    }
  });
  return hits.slice(0,25).join('\n');
})()"""
out = ev(JS, s)
print(out)
print('---- page url:', ev('location.href', s))
ws.close()
