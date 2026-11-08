import sys, json, time, re, urllib.parse
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


def search(query, engine='bing'):
    """Search via the real browser (curl-based engines are blocked)."""
    if engine == 'bing':
        url = 'https://www.bing.com/search?q=' + urllib.parse.quote(query)
    else:
        url = 'https://duckduckgo.com/?q=' + urllib.parse.quote(query)
    tid = cdp('Target.createTarget', {'url': url})['targetId']
    s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
    cdp('Page.enable', sid=s)
    time.sleep(7)
    raw = ev(r"""(()=>{
      const out=[];
      document.querySelectorAll('li.b_algo').forEach(li=>{
        const a=li.querySelector('h2 a');
        if(!a) return;
        const cite=li.querySelector('cite');
        let real = cite ? (cite.innerText||'').trim() : '';
        // Normalise the separators first: Bing uses U+203A (') but some
        // renders use '>' or '|'.
        real = real.replace(/\u203a/g, '>').replace(/\u00bb/g, '>')
                   .replace(/\s*[|]\s*/g, '>');
        // <cite> shows 'domain › path › more'. Rebuild a usable url:
        //   'supasportsman.com › index.php › contactus'
        //     -> https://supasportsman.com/index.php/contactus
        // The path segments are joined with '/' - they are separate path
        // pieces, not one slug, so replacing spaces with dashes (the old
        // behaviour) produced broken urls that never fetched.
        if(real){
          // Bing's <cite> NOW STARTS WITH 'https://' on many renders.
          // The old parser only stripped a leading http:// when the cite
          // had no scheme, so it produced 'https://https:/...' for every
          // result and EVERY fetch failed. That silently blinded the whole
          // company-reach funnel.
          //
          // Strip ANY scheme, then rebuild.
          const parts=real.split('>').map(x=>x.trim()).filter(Boolean);
          if(parts.length){
            let first=parts[0]
                       .replace(/^https?:\/\//i,'')
                       .replace(/^http:\/\//i,'')
                       .replace(/^www\./i,'');
            let dom=first.split('/')[0].replace(/[^a-zA-Z0-9.:-]/g,'');
            if(!dom){ return; }
            const path=parts.slice(1).map(x=>x.replace(/[^a-zA-Z0-9._~%-]/g,'-')).join('/');
            real='https://'+dom+(path?'/'+path:'');
          }
        }
        const href=a.getAttribute('href')||'';
        out.push((real||href)+' :: '+(a.innerText||'').trim().replace(/\\s+/g,' '));
      });
      return JSON.stringify([...new Set(out)].slice(0,14));
    })()""", s)
    try:
        items = json.loads(raw)
    except Exception:
        items = []
    out = []
    for it in items:
        url, _, title = it.partition(' :: ')
        out.append((url.strip(), title.strip()))
    try:
        cdp('Target.closeTarget', {'targetId': tid})
    except Exception:
        pass
    return out


if __name__ == '__main__':
    for q in sys.argv[1:] or ['"Nabil Al Raisi" Oman martial arts']:
        print('=== ', q)
        for h, t in search(q):
            print('   ', t[:62], '=>', h[:88])
