import sys, json, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect

# The buy-lead DETAIL pages may name the buyer company and show more than the
# list card does. If we can identify the actual buyer, we can reach them on
# their OWN site / email - no dependency on go4WorldBusiness's inquiry form.
TARGETS = [
    '/buyleads/1157651/wanted-:-taekwondo-belts',
    '/buyleads/1308114/wanted-:-boxing-accessories-like-hand-tie-gloves-head-guard',
    '/buyleads/1171526/wanted-:-martial-arts-belts-like-judo-belts',
    '/buyleads/1333286/wanted-:-soccer-football-jerseys-unit-units',
]

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


out = []
for path in TARGETS:
    url = 'https://www.go4worldbusiness.com' + path
    tid = cdp('Target.createTarget', {'url': url})['targetId']
    s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
    cdp('Page.enable', sid=s)
    time.sleep(20)
    txt = ev("""(()=>{
      const t = document.body ? document.body.innerText : '';
      // any outbound links that reveal the buyer
      const links = [...document.querySelectorAll('a[href^="http"]')]
        .map(a => a.href)
        .filter(h => !/go4worldbusiness\\.com/.test(h))
        .slice(0, 10);
      return JSON.stringify({text: t.slice(0, 2200), links});
    })()""", s)
    try:
        d = json.loads(txt)
    except Exception:
        d = {'text': str(txt)[:500], 'links': []}
    print('=' * 78)
    print(path)
    print(d['text'][:1700].replace('\n', ' | '))
    if d['links']:
        print('  OUTBOUND LINKS:', d['links'])
    out.append({'path': path, 'text': d['text'], 'links': d['links']})
    try:
        cdp('Target.closeTarget', {'targetId': tid})
    except Exception:
        pass

json.dump(out, open('/home/ubuntu/g4wb_rfq_details.json', 'w'), indent=2, ensure_ascii=False)
print()
print('saved -> /home/ubuntu/g4wb_rfq_details.json')
ws.close()
