import sys, json, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect

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
    deadline = time.time() + 45
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


URL = sys.argv[1]
tid = cdp('Target.createTarget', {'url': URL})['targetId']
s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
cdp('Page.enable', sid=s)
time.sleep(22)

# Fill memo1 with a short test then click Save, then inspect validation
print('fill:', ev("""(()=>{const e=document.querySelector('[name="edit_member_homepage[memo1]"]');if(!e)return 'no-field';const d=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value');d.set.call(e,'TEST INTRO');e.dispatchEvent(new Event('input',{bubbles:true}));return 'len='+e.value.length;})()""", s))
print('save:', ev("""(()=>{const bs=[...document.querySelectorAll('button,input[type=submit]')].filter(x=>((x.innerText||x.value||'').trim().toLowerCase()==='save'));if(!bs.length)return 'no-btn';bs[0].click();return 'clicked '+bs.length+' '+bs[0].tagName+' type='+(bs[0].getAttribute('type')||'')+' form='+(bs[0].form?bs[0].form.action:'nofrm');})()""", s))
time.sleep(11)
print('url after :', ev('location.href', s))
print('memo1 now :', ev("""(()=>{const e=document.querySelector('[name="edit_member_homepage[memo1]"]');return e?('len='+e.value.length+' | '+e.value.slice(0,60)):'<gone>';})()""", s))
print('validation:', ev("""(()=>{const t=document.body?document.body.innerText:'';const out=[];const re=/(this field cannot be empty|cannot be empty|required[^\\n]{0,60}|please\\s+[^\\n]{0,70}|error[^\\n]{0,70}|upload[^\\n]{0,60})/gi;let m;while((m=re.exec(t))&&out.length<8)out.push(m[0]);return out.join(' || ')||'none';})()""", s))
print('token:', ev("""(()=>{const t=document.querySelector('[name$="[_token]"]');return t?t.value.slice(0,12):'none';})()""", s))
ws.close()
