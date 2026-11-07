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


URL = 'https://www.go4worldbusiness.com/member/dashboard/company-profile'
tid = cdp('Target.createTarget', {'url': URL})['targetId']
s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
cdp('Page.enable', sid=s)
time.sleep(23)

# Open the category modal
print('open modal:', ev("""(()=>{
  const m=document.querySelector('#signup-category-modal');
  if(!m) return 'no-modal';
  m.classList.add('show'); m.style.display='block';
  const b=m.querySelector('.modal-backdrop');
  if(!b){const d=document.createElement('div');d.className='modal-backdrop fade show';document.body.appendChild(d);}
  return 'opened';
})()""", s))
time.sleep(6)
print('modal text:')
print(ev("""(()=>{const m=document.querySelector('#signup-category-modal');return m?(m.innerText||'').slice(0,900):'none';})()""", s))
print('modal inputs/buttons:')
print(ev("""(()=>{const m=document.querySelector('#signup-category-modal');if(!m)return 'none';
 const ins=[...m.querySelectorAll('input')].map(i=>(i.id||i.name||i.type)+'='+(i.value||'').slice(0,30));
 const btns=[...m.querySelectorAll('button,a')].map(b=>((b.innerText||'').trim()).slice(0,28)).filter(Boolean);
 const links=[...m.querySelectorAll('[data-id],[data-value],[data-category]')].map(e=>(e.tagName+'|'+(e.getAttribute('data-id')||e.getAttribute('data-value')||e.getAttribute('data-category'))+'|'+(e.textContent||'').trim().slice(0,40))).slice(0,15);
 return JSON.stringify({ins:ins.slice(0,12),btns:btns.slice(0,12),links:links},null,1);})()""", s))
print('save/search paths:', ev("""(()=>{const g=i=>{const e=document.getElementById(i);return e?e.value:'none';};return JSON.stringify({save:g('category-selection-save-path'),search:g('category-search-path')});})()""", s))
ws.close()
