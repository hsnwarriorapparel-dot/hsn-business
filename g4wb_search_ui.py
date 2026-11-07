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


tid = cdp('Target.createTarget', {'url': 'https://www.go4worldbusiness.com/list/latest/buyleads'})['targetId']
s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
cdp('Page.enable', sid=s)
time.sleep(24)

# Type in the real search box and submit, then read the resulting URL + list
for term in ['martial arts uniform', 'sportswear']:
    print('=== search:', term)
    print(' typed:', ev("""(()=>{
      const box=document.querySelector('input[name="searchText"]');
      if(!box) return 'no-box';
      box.focus();
      const d=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value');
      d.set.call(box,TERM);
      box.dispatchEvent(new Event('input',{bubbles:true}));
      box.dispatchEvent(new Event('change',{bubbles:true}));
      const form=box.closest('form');
      if(form){ form.submit(); return 'form-submitted'; }
      for(const t of ['keydown','keypress','keyup']) box.dispatchEvent(new KeyboardEvent(t,{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}));
      return 'typed';
    })()""".replace('TERM', json.dumps(term)), s))
    time.sleep(16)
    print(' url:', ev('location.href', s))
    print(' items:', ev("""(()=>{
      const t=document.body?document.body.innerText:'';
      const parts=t.split(/Wanted\\s*:/).slice(1);
      return parts.slice(0,6).map(p=>{
        const head=p.split('\\n').slice(0,2).join(' | ').trim().slice(0,100);
        const q=(p.match(/Quantity Required:\\s*([^\\n]+)/)||[])[1]||'';
        const bf=(p.match(/Buyer From\\s*([^\\n]+)/)||[])[1]||'';
        return head+' :: Q='+q.slice(0,22)+' :: '+bf.slice(0,22);
      }).join('\\n   ');
    })()""", s))
    print()
ws.close()
