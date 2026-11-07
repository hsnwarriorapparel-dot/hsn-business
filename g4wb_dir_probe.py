import sys, json, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect

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


URL = 'https://www.go4worldbusiness.com/buyers/Oman/martial-arts-gloves'
tid = cdp('Target.createTarget', {'url': URL})['targetId']
s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
cdp('Page.enable', sid=s)
time.sleep(24)

print('=== page head ===')
print(ev("""(()=>{
  const t=document.body?document.body.innerText:'';
  const i=t.search(/Martial Arts Gloves Buyers/);
  return t.slice(Math.max(0,i-150), i+1500).replace(/\\n+/g,' | ');
})()""", s))
print()
print('=== buyer entries: links + text ===')
print(ev("""(()=>{
  const out=[];
  document.querySelectorAll('a').forEach(a=>{
    const h=a.getAttribute('href')||'';
    const t=(a.innerText||'').trim().replace(/\\s+/g,' ');
    if(/\\/buyers\\//.test(h) && !/buyers\\/[^/]+\\/[^/]+$/.test(h) && t.length>3){
      out.push(t.slice(0,70)+'  =>  '+h.slice(0,110));
    }
  });
  return [...new Set(out)].slice(0,40).join('\\n')||'no buyer links matched';
})()""", s))
print()
print('=== pagination / country+category links ===')
print(ev("""(()=>{
  const out=[];
  document.querySelectorAll('a').forEach(a=>{
    const h=a.getAttribute('href')||'';
    const t=(a.innerText||'').trim().replace(/\\s+/g,' ');
    if(/\\/buyers\\//.test(h) && t.length>1 && t.length<40){
      out.push(t+' => '+h.slice(0,90));
    }
  });
  return [...new Set(out)].slice(0,35).join('\\n');
})()""", s))
try:
    cdp('Target.closeTarget', {'targetId': tid})
except Exception:
    pass
ws.close()
