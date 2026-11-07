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


URL = 'https://www.go4worldbusiness.com/member/dashboard/company-profile'
tid = cdp('Target.createTarget', {'url': URL})['targetId']
s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
cdp('Page.enable', sid=s)
time.sleep(23)

out = ev("""(async()=>{
  const r=await fetch('/countries/all-with-ids',{headers:{'X-Requested-With':'XMLHttpRequest'}});
  const j=JSON.parse(await r.text());
  const keys=Object.keys(j);
  const info={topKeys:keys};
  // find Pakistan anywhere
  const hits=[];
  const walk=(o,p)=>{
    if(o&&typeof o==='object'){
      for(const [k,v] of Object.entries(o)){
        if(typeof v==='string' && /pakistan/i.test(v)) hits.push(p+'.'+k+'='+v);
        else if(typeof v==='object') walk(v,p+'.'+k);
      }
    }
  };
  walk(j,'');
  info.hits=hits.slice(0,12);
  // shape of one country
  const c=j.countries||{};
  info.sampleShape=JSON.stringify(Object.entries(c).slice(0,2));
  const pkKey=Object.keys(c).find(k=>/pakistan/i.test(c[k]||''));
  info.pkKey=pkKey; info.pkName=pkKey?c[pkKey]:null;
  const m=j.codeToIdMap||{};
  info.pkId=pkKey?m[pkKey]:null;
  info.mapSample=JSON.stringify(Object.entries(m).slice(0,4));
  info.mapLen=Object.keys(m).length;
  info.kuwaitId=m['KW']; info.kuwaitName=c['KW'];
  info.pakLike=Object.entries(c).filter(([k,v])=>/pak|stan/i.test(String(v))).map(([k,v])=>k+'='+v+'#'+m[k]);
  info.codes=Object.keys(c).filter(k=>/^P/.test(k)).map(k=>k+'='+c[k]+'#'+m[k]);
  // is ANY spelling of Pakistan present? try values and also the raw JSON
  const raw=JSON.stringify(j.countries);
  info.hasPakistanRaw=/pakistan/i.test(raw);
  info.kCount=Object.keys(c).length;
  // neighbours that ARE present (Sialkot's likely mis-picks)
  info.neighbours=['India','China','Iran','Afghanistan','Uzbekistan'].map(n=>{
    const k=Object.keys(c).find(x=>c[x]===n); return n+'='+(k?k+'#'+m[k]:'ABSENT');});
  info.someEntries=Object.entries(c).slice(100,112).map(([k,v])=>k+'='+v+'#'+m[k]);
  return JSON.stringify(info);
})()""", s)
print(out)
ws.close()
