#!/usr/bin/env python3
"""Harvest buyers from the go4WorldBusiness BUYER DIRECTORY.

THE STRATEGY (2026-11-07)
-------------------------
go4WorldBusiness allows a JUNIOR member only ONE buyer inquiry per day
("As you are not a Premium GOLD/SILVER Member, you can only contact limited
number of buyers."). That makes the inquiry FORM a 1/day slot, not a channel.

But the site publishes a full BUYER DIRECTORY:
    https://www.go4worldbusiness.com/buyers/<COUNTRY>/<category-slug>
Each page lists many buy requirements, and each requirement names the buyer:
    "Contact : Nabil Al Raisi   Buyer Of Martial Arts Wear | Taekwondo"
    "Contact : Ritikmagiya       Buyer Of Boxing Gloves | Martial Arts Gloves"
The pages paginate with ?searchAfter=<cursor>, so the directory is deep.

A buyer NAME + COUNTRY + product category is enough to find the real importing
company on the open web and reach it on its OWN email - no platform limit, no
captcha, no daily cap. This script harvests that identity data; buyer_reach.py
turns it into contactable leads.

The category slugs come from the site's own category list, so the directory is
walked exactly the way the site intends.

Run:  python3 g4wb_dir_harvest.py --pages 3
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect

# SEPARATE FILE (2026-11-07) - see the note in g4wb_harvest_buyers.py.
OUT = '/home/ubuntu/g4wb_buyer_harvest_dir.json'

# Countries we sell into, with the slug the directory uses.
COUNTRIES = ['oman', 'egypt', 'malaysia', 'portugal', 'israel', 'united-arab-emirates',
             'saudi-arabia', 'qatar', 'kuwait', 'united-states', 'united-kingdom',
             'germany', 'france', 'spain', 'italy', 'netherlands', 'poland',
             'turkey', 'brazil', 'mexico', 'canada', 'australia', 'indonesia',
             'vietnam', 'thailand', 'philippines', 'nigeria', 'kenya', 'ghana',
             'south-africa', 'russia', 'ukraine', 'japan', 'south-korea']

# Category slugs that are OUR products. These come from the site's own
# "Fitness Equipment & Sports Goods" tree.
CATEGORIES = [
    'martial-arts-gloves', 'martial-arts-belts', 'martial-arts-mats',
    'martial-arts-goods-and-accessories', 'boxing-gloves', 'boxing-head-guards',
    'boxing-accessories', 'kick-pads', 'sports-goods-equipments', 'uniforms',
    'gym-gloves', 'sportswear', 'sports-apparel', 'team-uniforms', 'sports-jerseys',
    'football-jerseys', 'fight-gear', 'head-protection', 'mouth-guards',
    'shin-guards', 'hand-wraps', 'protective-equipment', 'sports-clothing',
    'karate-uniforms', 'taekwondo-uniforms', 'judo-uniforms', 'fight-wear',
    'mixed-martial-arts', 'self-defense', 'boxing-wear', 'fitness-equipment-sports-goods',
]

LEAD_RE = re.compile(r'/buylead/view/(\d+)/')


def load():
    try:
        return json.load(open(OUT))
    except Exception:
        return {}


def save(h):
    json.dump(h, open(OUT, 'w'), indent=2, ensure_ascii=False)


def main():
    pages = 3
    if '--pages' in sys.argv:
        pages = int(sys.argv[sys.argv.index('--pages') + 1])

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
    print('buyers already harvested: %d' % len(harvest))

    # Build the job list so consecutive runs hit different country/category
    # combinations (rotate by how many are already harvested).
    jobs = []
    for c in COUNTRIES:
        for cat in CATEGORIES:
            jobs.append((c, cat))
    # rotate the start so each run explores new ground
    offset = (len(harvest) * 7) % max(1, len(jobs))
    jobs = jobs[offset:] + jobs[:offset]
    # keep this run bounded
    jobs = jobs[:pages * 8]

    found_new = 0
    for country, cat in jobs:
        url = 'https://www.go4worldbusiness.com/buyers/%s/%s' % (country, cat)
        tid = cdp('Target.createTarget', {'url': url})['targetId']
        s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
        cdp('Page.enable', sid=s)
        time.sleep(17)
        raw = ev("""(()=>{
          const t=document.body?document.body.innerText:'';
          const out={};
          // split the page into requirement blocks
          const blocks=t.split(/Wanted\\s*:/).slice(1);
          out.blocks=blocks.length;
          const buyers=[];
          for(const b of blocks){
            const cm=b.match(/Contact\\s*:\\s*([^\\n|]{2,60})/);
            if(!cm) continue;
            const bm=b.match(/Buyer From\\s*([^\\n|]{2,40})/);
            const qm=b.match(/Quantity Required:\\s*([^\\n|]{2,40})/);
            const pm=b.match(/Product Name\\s*:?\\s*([^\\n|]{2,60})/);
            const dm=b.match(/([A-Z][a-z]{2}-\\d{2}-\\d{2})/);
            // category = the line after Contact that starts with 'Buyer Of'
            const lines=b.split('\\n');
            let catline='';
            for(let k=0;k<lines.length;k++){
              if(/Contact\\s*:/.test(lines[k]) && /Buyer Of/i.test(lines[k+1]||'')){
                catline=lines[k+1].replace(/VERIFIED|ARCHIVED|NEW|PREMIUM MEMBERS ONLY/gi,'').trim();
                break;
              }
            }
            // find this block's buylead link
            buyers.push({
              contact:cm[1].trim(),
              country:bm?bm[1].trim():'',
              qty:qm?qm[1].trim():'',
              product:pm?pm[1].trim():'',
              date:dm?dm[1]:'',
              category:catline
            });
          }
          out.buyers=buyers;
          // pagination cursor
          const nx=[...document.querySelectorAll('a')].find(a=>/Next/i.test(a.innerText||''));
          out.next= nx ? (nx.getAttribute('href')||'') : '';
          return JSON.stringify(out);
        })()""", s)
        try:
            d = json.loads(raw)
        except Exception:
            d = {'buyers': [], 'blocks': 0, 'next': ''}
        n_new = 0
        for b in d.get('buyers', []):
            if not b.get('contact'):
                continue
            # dedupe on name+country+product
            key = '%s|%s|%s' % (b['contact'].lower(), b.get('country', '').lower(),
                                (b.get('product') or '').lower())
            if any(key == v.get('dedupe') for v in harvest.values()):
                continue
            b['dedupe'] = key
            b['dir_country'] = country
            b['dir_category'] = cat
            b['harvested'] = time.strftime('%Y-%m-%d')
            # stable id from the dedupe key
            lid = str(abs(hash(key)) % 10 ** 9)
            b['id'] = lid
            b['href'] = 'https://www.go4worldbusiness.com/buyers/%s/%s' % (country, cat)
            harvest[lid] = b
            n_new += 1
            found_new += 1
        print('  %-14s %-36s blocks=%-3d buyers=%-3d new=%d%s' % (
            country, cat, d.get('blocks', 0), len(d.get('buyers', [])), n_new,
            '  ->next' if d.get('next') else ''))
        try:
            cdp('Target.closeTarget', {'targetId': tid})
        except Exception:
            pass
        save(harvest)

    save(harvest)
    print()
    print('NEW buyers this run: %d | total harvested: %d' % (found_new, len(harvest)))
    print('saved ->', OUT)
    ws.close()


if __name__ == '__main__':
    main()
