import sys, json, time, os
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect

TERMS = sys.argv[1:] or ['martial arts uniform']
OUT = '/home/ubuntu/g4wb_buyleads_found.json'

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

found = []
for term in TERMS:
    ev("""(()=>{
      const box=document.querySelector('input[name="searchText"]');
      if(!box) return 'no-box';
      box.focus();
      const d=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value');
      d.set.call(box,TERM);
      box.dispatchEvent(new Event('input',{bubbles:true}));
      const form=box.closest('form');
      if(form){ form.submit(); return 'ok'; }
      return 'no-form';
    })()""".replace('TERM', json.dumps(term)), s)
    time.sleep(17)
    raw = ev("""(()=>{
      const out=[];
      // each lead is a block; grab the title, meta and the 'Inquire Now' link
      document.querySelectorAll('a').forEach(a=>{
        const t=(a.innerText||'').trim();
        if(/inquir/i.test(t) && a.getAttribute('href')){
          let card=a;
          for(let i=0;i<6&&card;i++){card=card.parentElement;if(!card)break;
            const txt=(card.innerText||'');
            if(/Wanted|Quantity Required|Buyer From/.test(txt)&&txt.length>200)break;}
          const txt=(card.innerText||'').replace(/\\n+/g,' | ');
          out.push({href:a.getAttribute('href'), text:txt.slice(0,900)});
        }
      });
      // dedupe by href
      const seen=new Set(); const uniq=[];
      for(const o of out){ if(seen.has(o.href))continue; seen.add(o.href); uniq.push(o); }
      return JSON.stringify(uniq.slice(0,20));
    })()""", s)
    try:
        items = json.loads(raw)
    except Exception:
        items = []
    print('=== %s -> %d leads ===' % (term, len(items)))
    for it in items:
        found.append({'term': term, **it})
        # extract the key fields
        tx = it['text']
        title = tx.split(' | ')[0][:120]
        qty = ''
        for part in tx.split(' | '):
            if 'Quantity Required' in part:
                qty = part.split('Quantity Required')[1].strip()[:40]
        buyer = ''
        for part in tx.split(' | '):
            if 'Buyer From' in part:
                buyer = part.split('Buyer From')[1].strip()[:40]
        print('   %-64s | Q=%-22s | %s' % (title[:63], qty[:21], buyer[:26]))
        print('      %s' % it['href'][:100])

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(found, f, indent=2, ensure_ascii=False)
print()
print('saved ->', OUT, len(found), 'leads')
ws.close()
