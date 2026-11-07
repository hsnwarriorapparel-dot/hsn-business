import sys, json, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect

HREF = sys.argv[1] if len(sys.argv) > 1 else '/inquiries/send/buyleads/1333286/wanted-:-soccer-football-jerseys-unit-units'

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


URL = 'https://www.go4worldbusiness.com' + HREF
tid = cdp('Target.createTarget', {'url': URL})['targetId']
s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
cdp('Page.enable', sid=s)
time.sleep(24)

print('=== page ===')
print('url  :', ev('location.href', s))
print('title:', ev('document.title', s))
print()
print('=== form fields ===')
print(ev("""(()=>{
  const out=[];
  document.querySelectorAll('input,select,textarea').forEach(e=>{
    if(e.type==='hidden' && !/token|intent/i.test(e.name||'')) return;
    const lab=(e.name||e.id||e.placeholder||e.type);
    let extra='';
    if(e.tagName==='SELECT') extra=' opts:'+[...e.options].map(o=>o.value+'~'+o.text).slice(0,6).join(',');
    else if(e.type==='text'||e.tagName==='TEXTAREA') extra=' val='+(e.value||'').slice(0,40);
    out.push(lab+' |'+extra);
  });
  return out.slice(0,26).join('\\n');
})()""", s))
print()
print('=== buttons ===')
print(ev("""(()=>[...document.querySelectorAll('button,input[type=submit]')].map(b=>((b.innerText||b.value||'').trim().slice(0,40))+' | type='+(b.getAttribute('type')||'')).join('\\n'))()""", s))
print()
print('=== body (first 1200) ===')
print(ev("""(()=>{const t=document.body?document.body.innerText:'';const i=t.search(/Wanted|Inquir|Send|message/i);return t.slice(Math.max(0,i-100),i+1100);})()""", s))
ws.close()
