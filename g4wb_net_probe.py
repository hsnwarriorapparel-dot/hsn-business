import sys, json, time, threading
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect
import g4wb_listings as L

tabs = get_tabs()
gm = [t for t in tabs if 'mail.google' in t.get('url', '') and t.get('type') == 'page']
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

posts = []

tid = cdp('Target.createTarget', {'url': 'https://www.go4worldbusiness.com/member/dashboard/products/new/new/0'})['targetId']
s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
cdp('Page.enable', sid=s); cdp('DOM.enable', sid=s); cdp('Network.enable', sid=s)
time.sleep(22)

item = L.build()[0]
P = 'member_edit_prefproduct'

# 1. image
doc = cdp('DOM.getDocument', {}, s)
q = cdp('DOM.querySelector', {'nodeId': doc['root']['nodeId'],
                               'selector': 'input[type=file][name="%s[images][0][file][file]"]' % P}, s)
cdp('DOM.setFileInputFiles', {'files': ['/home/ubuntu/g4wb_assets/listings/gi.png'], 'nodeId': q['nodeId']}, s)
time.sleep(2)
ev("(()=>{const l=document.querySelector('label.imageUploadBtn');if(l){l.click();return 1;}return 0;})()", s)
time.sleep(7)
ev("(()=>{const b=document.querySelector('#cropBtn_0');if(b){b.click();return 1;}return 0;})()", s)
time.sleep(9)
ev("(()=>{const r=document.querySelector('#choose_primary_0');if(r){r.checked=true;return 1;}return 0;})()", s)

# 2. fields
vals = {
    '%s[prod][name]' % P: item['name'],
    '%s[prod][productGrade]' % P: item['grade'],
    '%s[prod][minPrice]' % P: str(item['min_price']),
    '%s[prod][maxPrice]' % P: str(item['max_price']),
    '%s[description]' % P: item['desc'],
    '%s[deliveryTimeQty]' % P: '25',
    '%s[deliveryTime]' % P: '25',
    '%s[packDetails]' % P: item['pack'],
    '%s[capacity]' % P: item['capacity'],
    '%s[prod][sellercode]' % P: item['seller_code'],
    '%s[prod][standards]' % P: item['standards'],
    '%s[prod][trademarkName]' % P: item['trademark'],
    '%s[prod][loadingPort]' % P: item['loading_port'],
    '%s[prod][usageOrApplication]' % P: item['usage'],
    '%s[brand]' % P: item['brand'],
    '%s[modelNo]' % P: item['model'],
    '%s[hsCode]' % P: item['hs_code'],
    '%s[prod][rateUnit]' % P: '18',
    '%s[prod][incoterm]' % P: '3',
    '%s[mfgCountry]' % P: 'Pakistan',
    '%s[deliveryTimeUnits]' % P: '18',
}
for i in range(1, 5):
    if i <= len(item['specs']): vals['%s[keySpec%d]' % (P, i)] = item['specs'][i-1]
    if i <= len(item['advantages']): vals['%s[keyAdv%d]' % (P, i)] = item['advantages'][i-1]
payload = json.dumps(vals, ensure_ascii=False)
js = """(()=>{const DATA=%s;const setVal=(el,v)=>{const pr=(el.tagName==='TEXTAREA')?window.HTMLTextAreaElement.prototype:window.HTMLInputElement.prototype;const d=Object.getOwnPropertyDescriptor(pr,'value');if(d&&d.set)d.set.call(el,v);else el.value=v;el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));};const rep=[];for(const [n,v] of Object.entries(DATA)){const el=document.querySelector('[name="'+n.replace(/"/g,'\\"')+'"]');if(!el){rep.push('MISS '+n);continue;}if(el.tagName==='SELECT'){let ok=false;for(const o of el.options){if(o.value===v||o.text===v){el.selectedIndex=o.index;ok=true;break;}}if(!ok){rep.push('NOOPT '+n);continue;}el.dispatchEvent(new Event('change',{bubbles:true}));}else{setVal(el,v);}rep.push('OK '+n);}const radios=[...document.querySelectorAll('input[name="member_edit_prefproduct[sample]"]')];if(radios.length){radios[0].checked=true;radios[0].dispatchEvent(new Event('change',{bubbles:true}));}return JSON.stringify(rep);})()""" % payload
rep = ev(js, s)
if not rep:
    print('JS FAILED - trying simpler form')
    print('  desc:', ev("(()=>{const e=document.querySelector('[name=\"member_edit_prefproduct[description]\"]');return e?('len='+e.value.length):'none';})()", s))
    print('  name:', ev("(()=>{const e=document.querySelector('[name=\"member_edit_prefproduct[prod][name]\"]');return e?e.value:'none';})()", s))
    raise SystemExit(1)
print('fields:', len(json.loads(rep)), 'problems:', [x for x in json.loads(rep) if x.startswith(('MISS','NOOPT'))])
ev("(()=>{const f=document.querySelector('form');if(f){f.removeAttribute('read_only');f.removeAttribute('novalidate');}return 1;})()", s)

ev("(()=>{const b=[...document.querySelectorAll('button,input[type=submit]')].find(x=>((x.innerText||x.value||'').trim().toLowerCase().replace(/\s+/g,' ')).startsWith('save'));if(b){b.click();return 'clicked';}return 'no-btn';})()", s)
time.sleep(20)
print('url  :', ev('location.href', s))
print('body head:', ev("(()=>{const t=document.body?document.body.innerText:'';return t.slice(600,1400);})()", s))
print('banner:', ev("(()=>{const t=document.body?document.body.innerText:'';const i=t.search(/correct the errors|errors below|please review|successfully|has been added/i);return i>=0?t.slice(i,i+300):'clean';})()", s))
print('POSTS:')
for st, u in posts[:14]: print('   ', st, u)
ws.close()
