#!/usr/bin/env python3
"""Deep-paginate the go4WorldBusiness buyer directory.

WHY (2026-11-07)
----------------
Every buyer-category directory page carries a "Next" link with a
`searchAfter` cursor:

    /find?searchText=martial-arts-mats&BuyersOrSuppliers=buyers
      &countryFilter[0]=oman&cityFilter[0]=&FindBuyers=&_format=html
      &searchAfter=WzE1LjMyNzMyNCwxNzUyMTI3OTMzOTg3XQ

Page 1 of a single country+category gives 50 requirements. The cursor
walks deeper - page 2 of oman/martial-arts-mats gives 41 more, and it keeps
going. So the real supply of martial-arts buyers is far larger than a
single page shows.

This script follows the cursor N pages deep for each country+category and
records every requirement it finds. It uses the SAME output file as
g4wb_dir_harvest.py (they are the same data, different depth) - the file
name is g4wb_buyer_harvest_dir.json.

Run:  python3 g4wb_deep_harvest.py --pages 3 --countries oman egypt malaysia
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect

OUT = '/home/ubuntu/g4wb_buyer_harvest_dir.json'

CATEGORIES = [
    'martial-arts-mats', 'martial-arts-gloves', 'martial-arts-belts',
    'martial-arts-goods-and-accessories', 'boxing-gloves', 'boxing-head-guards',
    'boxing-accessories', 'kick-pads', 'sports-goods-equipments',
    'sportswear', 'sports-apparel', 'uniforms', 'gym-gloves', 'fight-wear',
    'head-protection', 'mouth-guards', 'shin-guards', 'hand-wraps',
    'protective-equipment', 'sports-clothing', 'team-uniforms', 'sports-jerseys',
    'football-jerseys', 'karate-uniforms', 'taekwondo-uniforms',
    'fitness-equipment-sports-goods',
]

COUNTRIES = ['oman', 'egypt', 'malaysia', 'portugal', 'israel',
             'united-arab-emirates', 'saudi-arabia', 'qatar', 'kuwait',
             'united-states', 'united-kingdom', 'germany', 'france', 'spain',
             'italy', 'netherlands', 'poland', 'turkey', 'brazil', 'mexico',
             'canada', 'australia', 'indonesia', 'vietnam', 'thailand',
             'philippines', 'nigeria', 'kenya', 'ghana', 'south-africa',
             'russia', 'ukraine', 'japan', 'south-korea', 'pakistan']


def load():
    try:
        return json.load(open(OUT))
    except Exception:
        return {}


def save(h):
    json.dump(h, open(OUT, 'w'), indent=2, ensure_ascii=False)


def main():
    pages = 3
    countries = COUNTRIES
    cats = CATEGORIES
    args = sys.argv[1:]
    if '--pages' in args:
        pages = int(args[args.index('--pages') + 1])
    if '--countries' in args:
        i = args.index('--countries')
        countries = []
        for a in args[i + 1:]:
            if a.startswith('--'):
                break
            countries.append(a)
    if '--cats' in args:
        i = args.index('--cats')
        cats = []
        for a in args[i + 1:]:
            if a.startswith('--'):
                break
            cats.append(a)

    tabs = get_tabs()
    gm = [t for t in tabs if 'mail.google' in (t.get('url') or '') and t.get('type') == 'page']
    if not gm:
        print('NO BROWSER TAB')
        return
    ws = connect(gm[0]); _n = [0]

    def cdp(m, p=None, sid=None):
        _n[0] += 1
        mid = _n[0]
        msg = {'id': mid, 'method': m, 'params': p or {}}
        if sid:
            msg['sessionId'] = sid
        ws.send(json.dumps(msg))
        t = time.time() + 55
        while time.time() < t:
            d = json.loads(ws.recv())
            if d.get('id') == mid:
                if 'error' in d:
                    raise RuntimeError(d['error'])
                return d.get('result', {})
        raise TimeoutError(m)

    def ev(e, s):
        r = cdp('Runtime.evaluate', {'expression': e, 'returnByValue': True,
                                     'awaitPromise': True}, sid=s)
        if r.get('exceptionDetails'):
            return 'JS_ERR: ' + str(r['exceptionDetails'])[:180]
        return r.get('result', {}).get('value')

    harvest = load()
    print('harvest so far: %d' % len(harvest))

    total_new = 0
    total_pages = 0
    for country in countries:
        for cat in cats:
            url = 'https://www.go4worldbusiness.com/buyers/%s/%s.html' % (country, cat)
            for page in range(pages):
                tid = cdp('Target.createTarget', {'url': url})['targetId']
                s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
                cdp('Page.enable', sid=s)
                time.sleep(17)
                raw = ev("""(()=>{
                  const t = document.body ? document.body.innerText : '';
                  const blocks = t.split(/Wanted\\s*:/).slice(1);
                  const buyers = [];
                  for (const b of blocks) {
                    const cm = b.match(/Contact\\s*:\\s*([^\\n|]{2,60})/);
                    if (!cm) continue;
                    const bm = b.match(/Buyer From\\s*([^\\n|]{2,40})/);
                    const qm = b.match(/Quantity Required:\\s*([^\\n|]{2,40})/);
                    const pm = b.match(/Product Name\\s*:?\\s*([^\\n|]{2,60})/);
                    const dm = b.match(/([A-Z][a-z]{2}-\\d{2}-\\d{2})/);
                    const lines = b.split('\\n');
                    let catline = '';
                    for (let k = 0; k < lines.length; k++) {
                      if (/Contact\\s*:/.test(lines[k]) && /Buyer Of/i.test(lines[k+1]||'')) {
                        catline = lines[k+1].replace(/VERIFIED|ARCHIVED|NEW|PREMIUM MEMBERS ONLY/gi,'').trim();
                        break;
                      }
                    }
                    buyers.push({
                      contact: cm[1].trim(),
                      country: bm ? bm[1].trim() : '',
                      qty: qm ? qm[1].trim() : '',
                      product: pm ? pm[1].trim() : '',
                      date: dm ? dm[1] : '',
                      category: catline
                    });
                  }
                  const nx = [...document.querySelectorAll('a')]
                    .find(a => /Next/i.test(a.innerText || '') && (a.getAttribute('href')||'').indexOf('searchAfter') >= 0);
                  return JSON.stringify({buyers: buyers, blocks: blocks.length,
                    next: nx ? (nx.getAttribute('href')||'') : ''});
                })()""", s)
                try:
                    d = json.loads(raw)
                except Exception:
                    d = {'buyers': [], 'blocks': 0, 'next': ''}
                n_new = 0
                for b in d.get('buyers', []):
                    if not b.get('contact'):
                        continue
                    key = '%s|%s|%s' % (b['contact'].lower(), b.get('country', '').lower(),
                                        (b.get('product') or '').lower())
                    if any(key == v.get('dedupe') for v in harvest.values()):
                        continue
                    b['dedupe'] = key
                    b['dir_country'] = country
                    b['dir_category'] = cat
                    b['page'] = page + 1
                    b['harvested'] = time.strftime('%Y-%m-%d')
                    b['id'] = str(abs(hash(key)) % 10 ** 9)
                    b['href'] = 'https://www.go4worldbusiness.com/buyers/%s/%s.html' % (country, cat)
                    harvest[b['id']] = b
                    n_new += 1
                    total_new += 1
                total_pages += 1
                print('  %-9s %-30s p%d blocks=%-3d new=%-3d%s'
                      % (country, cat[:29], page + 1, d.get('blocks', 0), n_new,
                         '  ->next' if d.get('next') else '  (last page)'))
                try:
                    cdp('Target.closeTarget', {'targetId': tid})
                except Exception:
                    pass
                if not d.get('next'):
                    break
                # follow the cursor
                nxt = d['next']
                if nxt.startswith('/'):
                    nxt = 'https://www.go4worldbusiness.com' + nxt
                url = nxt
                time.sleep(1)
            save(harvest)

    save(harvest)
    print()
    print('pages read: %d | NEW: %d | total harvested: %d' % (total_pages, total_new, len(harvest)))
    print('saved ->', OUT)
    ws.close()


if __name__ == '__main__':
    main()
