import sys, json, time, re
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


# A buyer profile: does it expose contact details, or only via inquiry?
URL = 'https://www.go4worldbusiness.com/member/3682705/nargis-impex'
tid = cdp('Target.createTarget', {'url': URL})['targetId']
s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
cdp('Page.enable', sid=s)
time.sleep(22)

print('=== buyer public profile ===')
print(ev("""(()=>{
  const t=document.body?document.body.innerText:'';
  return t.slice(0,1600).replace(/\\n+/g,' | ');
})()""", s))
print()
print('=== contact-ish links ===')
print(ev("""(()=>{
  const out=[];
  document.querySelectorAll('a,button').forEach(a=>{
    const t=(a.innerText||a.getAttribute('aria-label')||'').trim();
    if(/contact|inquir|email|message|chat|call/i.test(t)){
      const h=a.getAttribute('href')||'';
      out.push(t.slice(0,40)+' => '+h.slice(0,110));
    }
  });
  return [...new Set(out)].slice(0,20).join('\\n')||'none';
})()""", s))
print()
print('=== any visible email / phone ===')
print(ev("""(()=>{
  const t=document.body?document.body.innerText:'';
  const m=t.match(/[\\w.+-]+@[\\w.-]+\\.\\w{2,}/g);
  const p=t.match(/\\+?\\d[\\d\\s().-]{8,}\\d/g);
  return JSON.stringify({emails:m?m.slice(0,5):[], phones:p?p.slice(0,5):[]});
})()""", s))
try:
    cdp('Target.closeTarget', {'targetId': tid})
except Exception:
    pass
ws.close()
