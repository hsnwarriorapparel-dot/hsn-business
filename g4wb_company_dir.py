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


# The 'Buyer Of X' links on the directory page point at a COMPANY LIST page.
for url in ['https://www.go4worldbusiness.com/buyers/oman/boxing-gloves.html',
            'https://www.go4worldbusiness.com/buyers/oman/sports-goods-equipments.html']:
    tid = cdp('Target.createTarget', {'url': url})['targetId']
    s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
    cdp('Page.enable', sid=s)
    time.sleep(20)
    print('=' * 72)
    print(url)
    print(ev("""(()=>{
      const t=document.body?document.body.innerText:'';
      const i=t.search(/Buyers, Importers|Buyers & Importers|Find Verified/);
      return t.slice(Math.max(0,i-120), i+1100).replace(/\\n+/g,' | ');
    })()""", s))
    print()
    print('--- company links ---')
    print(ev("""(()=>{
      const out=[];
      document.querySelectorAll('a').forEach(a=>{
        const h=a.getAttribute('href')||'';
        const t=(a.innerText||'').trim().replace(/\\s+/g,' ');
        if(/\\/member\\/view\\/|\\/companies\\/|\\/suppliers\\//.test(h) && t.length>2){
          out.push(t.slice(0,44)+' => '+h.slice(0,90));
        }
      });
      return [...new Set(out)].slice(0,22).join('\\n')||'no company links';
    })()""", s))
    try:
        cdp('Target.closeTarget', {'targetId': tid})
    except Exception:
        pass
ws.close()
