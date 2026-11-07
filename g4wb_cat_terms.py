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
        return 'JS_ERR: ' + str(r['exceptionDetails'])[:300]
    return r.get('result', {}).get('value')


URL = 'https://www.go4worldbusiness.com/member/dashboard/company-profile'
tid = cdp('Target.createTarget', {'url': URL})['targetId']
s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
cdp('Page.enable', sid=s)
time.sleep(23)

# Search the categories we actually need
TERMS = ['martial arts', 'boxing', 'sportswear', 'sports', 'apparel', 'clothing',
         'glove', 'belt', 'headgear', 'shin', 'karate', 'judo', 'taekwondo',
         'uniform', 'fight', 'training', 'protection', 't-shirt']
js = """(async()=>{
  const terms=TERMS;
  const out={};
  for(const t of terms){
    try{
      const r=await fetch('/signup/ajax/category-search?q='+encodeURIComponent(t),{headers:{'X-Requested-With':'XMLHttpRequest'}});
      const j=JSON.parse(await r.text());
      out[t]=j;
    }catch(e){out[t]='ERR '+e;}
  }
  return JSON.stringify(out);
})()""".replace('TERMS', json.dumps(TERMS))
res = ev(js, s)
try:
    d = json.loads(res)
    for t, v in d.items():
        if isinstance(v, list) and v:
            for item in v[:6]:
                print("  %-12s %-52s %s" % (t, item['label'], item['value']))
except Exception as e:
    print('parse err', e, str(res)[:800])
ws.close()
