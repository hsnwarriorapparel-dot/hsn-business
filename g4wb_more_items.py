import sys, json, time, re
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


URL = 'https://www.go4worldbusiness.com/inquiries/send/buyleads/1138043/wanted-:-karate-black-master-belt'
tid = cdp('Target.createTarget', {'url': URL})['targetId']
s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
cdp('Page.enable', sid=s)
time.sleep(24)

# The "More Items that may be of Your interest" carousel holds ARCHIVED leads.
raw = ev("""(()=>{
  const out=[];
  document.querySelectorAll('a[href*="/inquiries/send/buyleads/"]').forEach(a=>{
    const h=a.getAttribute('href')||'';
    let card=a;
    for(let i=0;i<7&&card;i++){
      card=card.parentElement; if(!card) break;
      const t=(card.innerText||'');
      if(/Quantity Required/.test(t) && t.length>60) break;
    }
    const t=(card.innerText||'').replace(/\\n+/g,' | ');
    out.push({href:h, text:t.slice(0,420)});
  });
  const seen=new Set(); const uniq=[];
  for(const o of out){ if(seen.has(o.href))continue; seen.add(o.href); uniq.push(o); }
  return JSON.stringify(uniq.slice(0,40));
})()""", s)
try:
    items = json.loads(raw)
except Exception:
    print('parse fail:', str(raw)[:300]); items = []

print('=== carousel / more-items buyleads:', len(items), '===')
RELEV = re.compile(r'martial|karate|judo|taekwondo|tae kwon|bjj|jiu|boxing|fight|mma|gym|sport|t-?shirt|uniform|shorts|hoodie|track|apparel|clothing|jersey|mat|belt|protective|gloves|headgear|shin', re.I)
hits = []
for it in items:
    slug = it['href'].split('wanted-:-')[-1].replace('-', ' ')
    tx = it['text']
    qty = buyer = date = src = ''
    for part in tx.split(' | '):
        p = part.strip()
        if p.startswith('Quantity Required'): qty = p.split(':')[-1].strip()
        elif p.startswith('Buyer From'): buyer = p.split(':')[-1].strip()
        elif re.match(r'^[A-Z][a-z]{2}-\d{2}-\d{2}$', p): date = p
        elif 'Looking for suppliers from' in p: src = p.split(':')[-1].strip()
    arch = 'ARCHIVED' in tx
    ok = RELEV.search(slug)
    hits.append({'slug': slug, 'href': it['href'], 'qty': qty, 'buyer': buyer,
                 'date': date, 'from': src, 'archived': arch, 'relevant': bool(ok), 'text': tx[:400]})
    if ok:
        print('  %-46s | %-16s | %-20s | %-9s | %s' % (slug[:45], qty[:15], buyer[:19], date, 'ARCHIVED' if arch else 'live'))

print()
rel = [h for h in hits if h['relevant']]
print('relevant:', len(rel))
# big orders first
def qn(s):
    s = (s or '').replace(',', '')
    m = re.search(r'([\d.]+)\s*(Pieces|Units|pcs|Unit/Units)', s, re.I)
    if not m: return 0
    return int(float(m.group(1)))
rel.sort(key=lambda h: -qn(h['qty']))
print()
print('=== biggest relevant RFQs ===')
for h in rel[:10]:
    print('  %6d | %-42s | %-18s | %-9s | %s' % (qn(h['qty']), h['slug'][:41], h['buyer'][:17], h['date'],
          'ARCHIVED' if h['archived'] else 'LIVE'))
json.dump(hits, open('/home/ubuntu/g4wb_more_items.json', 'w'), indent=2, ensure_ascii=False)
print('\nsaved -> /home/ubuntu/g4wb_more_items.json')
ws.close()
