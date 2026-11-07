#!/usr/bin/env python3
"""Harvest BUYER COMPANIES from the go4WorldBusiness buyer directory.

THE REAL UNLOCK (2026-11-07)
----------------------------
Two directory shapes exist, and only one of them is useful:

  /buyers/<country>/<category-slug>          -> buy REQUIREMENTS (a lead)
  /buyers/<country>/<category-slug>.html     -> BUYER COMPANIES (the target)

The .html variant lists the actual company names with their own profile URL:
    Gloves Up Fitness Club          => /member/view/3969100/gloves-up-fitness-club.html
    Bid Bid Wholesale & Retail      => /member/view/3193522/bid-bid-wholesale-retail.html
    Supa Sportsman LLC              => /member/view/1484424/supa-sportsman-llc.html
    Muscat Sports LLC               => /member/view/3994822/muscat-sports-llc.html
    Caresun Sportswear              => /member/view/4145287/caresun-sportswear.html

A COMPANY NAME is a far better search key than a person's name: the company
has a website, and the website has a sales email. That is how the 1/day
go4WorldBusiness inquiry limit gets bypassed - we find the same buyer on the
open web and contact them directly.

This script harvests the company names. buyer_reach.py then finds each
company's site and email.
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect

OUT = '/home/ubuntu/g4wb_company_harvest.json'

COUNTRIES = ['oman', 'egypt', 'malaysia', 'portugal', 'israel',
             'united-arab-emirates', 'saudi-arabia', 'qatar', 'kuwait',
             'united-states', 'united-kingdom', 'germany', 'france', 'spain',
             'italy', 'netherlands', 'poland', 'turkey', 'brazil', 'mexico',
             'canada', 'australia', 'indonesia', 'vietnam', 'thailand',
             'philippines', 'nigeria', 'kenya', 'ghana', 'south-africa',
             'russia', 'ukraine', 'japan', 'south-korea', 'pakistan']

# Category slugs from the site's own "Fitness Equipment & Sports Goods" tree.
CATEGORIES = [
    'boxing-gloves', 'boxing-head-guards', 'boxing-accessories', 'kick-pads',
    'martial-arts-gloves', 'martial-arts-belts', 'martial-arts-mats',
    'martial-arts-goods-and-accessories', 'sports-goods-equipments',
    'sportswear', 'sports-apparel', 'uniforms', 'gym-gloves', 'fight-wear',
    'head-protection', 'mouth-guards', 'shin-guards', 'hand-wraps',
    'protective-equipment', 'sports-clothing', 'team-uniforms', 'sports-jerseys',
    'football-jerseys', 'karate-uniforms', 'taekwondo-uniforms',
    'fitness-equipment-sports-goods', 'gym-equipment', 'sports-accessories',
]

MEMBER_RE = re.compile(r'/member/view/(\d+)/([^\'"<>]+?)\.html')


def load():
    try:
        return json.load(open(OUT))
    except Exception:
        return {}


def save(h):
    json.dump(h, open(OUT, 'w'), indent=2, ensure_ascii=False)


def main():
    pages = 4
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
    print('buyer companies already harvested: %d' % len(harvest))

    jobs = []
    for c in COUNTRIES:
        for cat in CATEGORIES:
            jobs.append((c, cat))
    offset = (len(harvest) * 11) % max(1, len(jobs))
    jobs = jobs[offset:] + jobs[:offset]
    jobs = jobs[:pages * 8]

    new = 0
    for country, cat in jobs:
        url = 'https://www.go4worldbusiness.com/buyers/%s/%s.html' % (country, cat)
        tid = cdp('Target.createTarget', {'url': url})['targetId']
        s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
        cdp('Page.enable', sid=s)
        time.sleep(16)
        raw = ev("""(()=>{
          const out=[];
          document.querySelectorAll('a[href*="/member/view/"]').forEach(a=>{
            const h=a.getAttribute('href')||'';
            const t=(a.innerText||'').trim().replace(/\\s+/g,' ');
            if(t && t.length>1 && t.length<90) out.push(h+' :: '+t);
          });
          return JSON.stringify([...new Set(out)]);
        })()""", s)
        try:
            rows = json.loads(raw)
        except Exception:
            rows = []
        n = 0
        for r in rows:
            href, _, name = r.partition(' :: ')
            m = MEMBER_RE.search(href)
            if not m:
                continue
            mid_, slug = m.group(1), m.group(2)
            if mid_ in harvest:
                continue
            harvest[mid_] = {'id': mid_, 'company': name, 'slug': slug,
                             'href': 'https://www.go4worldbusiness.com' + href,
                             'dir_country': country, 'dir_category': cat,
                             'harvested': time.strftime('%Y-%m-%d')}
            n += 1
            new += 1
        print('  %-10s %-34s companies=%-3d new=%d' % (country, cat[:33], len(rows), n))
        try:
            cdp('Target.closeTarget', {'targetId': tid})
        except Exception:
            pass
        save(harvest)

    save(harvest)
    print()
    print('NEW companies this run: %d | total: %d' % (new, len(harvest)))
    print('saved ->', OUT)
    ws.close()


if __name__ == '__main__':
    main()
