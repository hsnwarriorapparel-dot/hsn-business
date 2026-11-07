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


URL = 'https://www.go4worldbusiness.com/buyleads/1157651/wanted-:-taekwondo-belts'
tid = cdp('Target.createTarget', {'url': URL})['targetId']
s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
cdp('Page.enable', sid=s)
time.sleep(22)

links = ev("""(()=>{
  const out=[];
  document.querySelectorAll('a').forEach(a=>{
    const h=a.getAttribute('href')||'';
    const t=(a.innerText||'').trim().replace(/\\s+/g,' ');
    if(!h) return;
    if(/buylead|category|supplier|member|companies|search/i.test(h)){
      out.push(t.slice(0,46)+'  =>  '+h.slice(0,120));
    }
  });
  return [...new Set(out)].slice(0,70).join('\\n');
})()""", s)
print('=== NAV / CATEGORY LINKS ===')
print(links)

print()
print('=== "Find Verified ... Buyers" page link ===')
print(ev("""(()=>{
  const a=[...document.querySelectorAll('a')].find(x=>/Find Verified/i.test(x.innerText||''));
  return a ? a.getAttribute('href') : 'none';
})()""", s))

print()
print('=== suggestion links (category slugs) ===')
print(ev("""(()=>{
  const out=[];
  document.querySelectorAll('a').forEach(a=>{
    const t=(a.innerText||'').trim();
    if(/^(Belts|Belt Buckles|Leather Belts|Gym Belts|Martial Arts|Industrial|Suggestions)$/i.test(t) ||
       /Belts|Gloves|Mats|Uniforms|Karate|Taekwondo|Boxing|Judo/i.test(t)){
      const h=a.getAttribute('href')||'';
      if(h && !/inquiries/.test(h)) out.push(t.slice(0,34)+' => '+h.slice(0,100));
    }
  });
  return [...new Set(out)].slice(0,30).join('\\n');
})()""", s))
try:
    cdp('Target.closeTarget', {'targetId': tid})
except Exception:
    pass
ws.close()
