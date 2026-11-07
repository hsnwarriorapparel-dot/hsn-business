import sys, json, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect
import g4wb_fill_profile as F

tabs = get_tabs()
gm = [t for t in tabs if 'mail.google' in t.get('url', '') and t.get('type') == 'page']
if not gm:
    print('NO BROWSER TAB'); sys.exit(1)
ws = connect(gm[0])
_n = [0]

def cdp(method, params=None, sid=None):
    _n[0] += 1
    mid = _n[0]
    msg = {'id': mid, 'method': method, 'params': params or {}}
    if sid:
        msg['sessionId'] = sid
    ws.send(json.dumps(msg))
    deadline = time.time() + 60
    while time.time() < deadline:
        data = json.loads(ws.recv())
        if data.get('id') == mid:
            if 'error' in data:
                raise RuntimeError(data['error'])
            return data.get('result', {})
    raise TimeoutError(method)

def ev(expr, sid):
    r = cdp('Runtime.evaluate', {'expression': expr, 'returnByValue': True}, sid)
    return r.get('result', {}).get('value')

URL = 'https://www.go4worldbusiness.com/member/dashboard/homepage'
tid = cdp('Target.createTarget', {'url': URL})['targetId']
s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
cdp('Page.enable', sid=s)
cdp('DOM.enable', sid=s)
time.sleep(22)

FILES = [
    ('member_edit_homepage_logoUrl', '/home/ubuntu/g4wb_assets/logo.png'),
    ('member_edit_homepage_image1Url', '/home/ubuntu/g4wb_assets/factory.jpg'),
]
for name, path in FILES:
    doc = cdp('DOM.getDocument', {}, s)
    q = cdp('DOM.querySelector', {'nodeId': doc['root']['nodeId'], 'selector': 'input[type=file][name="%s"]' % name}, s)
    nid = q.get('nodeId', 0)
    print(name, 'nodeId=', nid)
    if nid:
        try:
            cdp('DOM.setFileInputFiles', {'files': [path], 'nodeId': nid}, s)
            print('  set:', path)
        except Exception as e:
            print('  ERR', e)
    time.sleep(3)

ev("""(()=>{const fs=[...document.querySelectorAll('input[type=file]')];fs.forEach(f=>{f.dispatchEvent(new Event('change',{bubbles:true}));f.dispatchEvent(new Event('input',{bubbles:true}));});return 'dispatched '+fs.length;})()""", s)
time.sleep(5)
print('file state:', ev("""(()=>[...document.querySelectorAll('input[type=file]')].map(f=>f.name+'='+(f.files&&f.files.length?f.files[0].name:'none')).join(' | '))()""", s))

payload = json.dumps(F.HOMEPAGE, ensure_ascii=False)
fill_js = """(()=>{
  const DATA=%s;
  const setVal=(el,v)=>{
    const d=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value');
    d.set.call(el,v);
    el.dispatchEvent(new Event('input',{bubbles:true}));
    el.dispatchEvent(new Event('change',{bubbles:true}));
  };
  const rep=[];
  for(const [name,val] of Object.entries(DATA)){
    const el=document.querySelector('[name="'+name.replace(/"/g,'\\"')+'"]');
    if(!el){rep.push('MISS '+name);continue;}
    setVal(el,val); rep.push('OK '+name+' len='+el.value.length);
  }
  return JSON.stringify(rep);
})()""" % payload
print('memos:', ev(fill_js, s))
print('save:', ev("""(()=>{const b=[...document.querySelectorAll('button,input[type=submit]')].find(x=>((x.innerText||x.value||'').trim().toLowerCase()==='save'));if(!b)return 'no-btn';b.click();return 'clicked';})()""", s))
time.sleep(16)
print('url:', ev('location.href', s))
print('memo1:', ev("""(()=>{const e=document.querySelector('[name="edit_member_homepage[memo1]"]');return e?('len='+e.value.length+' | '+e.value.slice(0,50)):'<gone>';})()""", s))
print('logo hidden:', ev("""(()=>{const h=document.querySelector('[name="edit_member_homepage[logoUrl]"]');return h?('val='+h.value.slice(0,70)):'none';})()""", s))
print('notice:', ev("""(()=>{const t=document.body?document.body.innerText:'';const m=t.match(/(under review|being reviewed|cannot be empty)/gi);return m?m.slice(0,4).join(' || '):'none';})()""", s))
ws.close()
