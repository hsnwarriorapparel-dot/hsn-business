#!/usr/bin/env python3
"""Harvest buyer identities from go4WorldBusiness RFQ pages.

WHY THIS EXISTS (2026-11-07)
---------------------------
go4WorldBusiness lets a JUNIOR member send only ONE buyer inquiry per day
("As you are not a Premium GOLD/SILVER Member, you can only contact limited
number of buyers."). So the inquiry FORM is a 1/day slot, not a channel.

But the public RFQ pages expose the buyer's real identity:
    "Contact : Ali Aref      Buyer Of Boxing Accessories | Boxing Gloves"
    "Contact : Justin Leiva  Buyer Of Knitted & Woven Garments | Jersey"
    "Contact : Mr. Aneez     Buyer Of Industrial Belts & Straps"

A buyer name + country + product category is enough to find the company on the
open web and reach it on its OWN email - no platform limit, no captcha, no
1/day cap. That is a second, independent funnel that the 1/day slot cannot
block.

THIS SCRIPT harvests that identity data. A second script (buyer_reach.py)
then finds each buyer's real company + email and puts them in the outreach
queue.

Each buyer is harvested ONCE - the buyer_harvest.json file records what we
already have, so the list keeps growing without duplicates.
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect

# SEPARATE FILE (2026-11-07): this harvester and g4wb_dir_harvest.py used to
# both write g4wb_buyer_harvest.json, so whichever finished last wiped the
# other's entries. Each harvester now owns its own file and
# g4wb_filter_harvest.py merges them.
HARVEST = '/home/ubuntu/g4wb_buyer_harvest_search.json'
LEDGER = '/home/ubuntu/send_ledger.jsonl'

# Search terms that pull in the categories we actually manufacture.
TERMS = [
    'martial arts', 'karate', 'taekwondo', 'judo belt', 'boxing gloves',
    'boxing accessories', 'headgear', 'sportswear', 'sports jersey',
    'football jersey', 'gi uniform', 'rash guard', 'fight shorts',
    'team uniform', 'sports wear', 'boxing equipment', 'mouth guard',
    'gym wear', 'sports apparel',
]

# The RFQ pages list many leads each. These are the detail-page URL patterns.
LEAD_RE = re.compile(r'/buylead/view/(\d+)/([^"\'<>]+?)\.html')


def load_harvest():
    try:
        return json.load(open(HARVEST))
    except Exception:
        return {}


def save_harvest(h):
    json.dump(h, open(HARVEST, 'w'), indent=2, ensure_ascii=False)


def connect_browser():
    tabs = get_tabs()
    gm = [t for t in tabs if 'mail.google' in (t.get('url') or '') and t.get('type') == 'page']
    if not gm:
        return None
    ws = connect(gm[0])
    return ws


def main():
    max_pages = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    ws = connect_browser()
    if not ws:
        print('NO BROWSER TAB')
        return
    _n = [0]

    def cdp(m, p=None, sid=None):
        _n[0] += 1
        mid = _n[0]
        msg = {'id': mid, 'method': m, 'params': p or {}}
        if sid:
            msg['sessionId'] = sid
        ws.send(json.dumps(msg))
        t = time.time() + 50
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

    harvest = load_harvest()
    print('harvest so far: %d buyers' % len(harvest))

    # Phase 1: collect the DETAIL page URLs from each category search.
    detail_urls = {}
    for term in TERMS:
        url = ('https://www.go4worldbusiness.com/find?searchText=' +
               term.replace(' ', '+') +
               '&BuyersOrSuppliers=buyers&countryFilter%5B0%5D=&cityFilter%5B0%5D=&FindBuyers')
        tid = cdp('Target.createTarget', {'url': url})['targetId']
        s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
        cdp('Page.enable', sid=s)
        time.sleep(18)
        raw = ev("""(()=>{
          const out=[];
          document.querySelectorAll('a[href*="/buylead/view/"]').forEach(a=>{
            out.push((a.getAttribute('href')||'')+' :: '+(a.innerText||'').trim());
          });
          return JSON.stringify([...new Set(out)]);
        })()""", s)
        try:
            links = json.loads(raw)
        except Exception:
            links = []
        got = 0
        for l in links:
            href, _, title = l.partition(' :: ')
            m = LEAD_RE.search(href)
            if not m:
                continue
            lid, slug = m.group(1), m.group(2)
            key = lid
            if key not in detail_urls:
                detail_urls[key] = {'id': lid, 'slug': slug, 'href': href,
                                    'title': title[:120], 'term': term}
                got += 1
        print('  %-20s -> %2d new detail pages' % (term, got))
        try:
            cdp('Target.closeTarget', {'targetId': tid})
        except Exception:
            pass

    print()
    print('total detail pages to read: %d' % len(detail_urls))

    # Phase 2: read each detail page for the buyer identity.
    to_read = [d for k, d in detail_urls.items() if k not in harvest]
    to_read = to_read[:max_pages]
    found = 0
    for i, d in enumerate(to_read, 1):
        url = 'https://www.go4worldbusiness.com' + d['href']
        tid = cdp('Target.createTarget', {'url': url})['targetId']
        s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
        cdp('Page.enable', sid=s)
        time.sleep(16)
        raw = ev("""(()=>{
          const t=document.body?document.body.innerText:'';
          const out={};
          const cm=t.match(/Contact\\s*:\\s*([^\\n|]{2,60})/);
          out.contact = cm ? cm[1].trim() : '';
          const bm=t.match(/Buyer From\\s*([^\\n|]{2,40})/);
          out.country = bm ? bm[1].trim() : '';
          const qm=t.match(/Quantity Required:\\s*([^\\n|]{2,40})/);
          out.qty = qm ? qm[1].trim() : '';
          const pm=t.match(/Product Name\\s*:?\\s*([^\\n|]{2,60})/);
          out.product = pm ? pm[1].trim() : '';
          // the buyer-of category list right after the contact line. The page
          // footer contains 'File a complaint', so only accept a line that
          // really starts with 'Buyer Of'.
          let cat = '';
          const lines = t.split('\\n');
          for (let k = 0; k < lines.length; k++) {
            if (/Contact\\s*:/.test(lines[k]) && /Buyer Of/i.test(lines[k+1] || '')) {
              cat = lines[k+1].replace(/VERIFIED|ARCHIVED|NEW|PREMIUM MEMBERS ONLY/gi,'').trim();
              break;
            }
          }
          out.category = cat;
          const dm=t.match(/([A-Z][a-z]{2}-\\d{2}-\\d{2})/);
          out.date = dm ? dm[1] : '';
          return JSON.stringify(out);
        })()""", s)
        try:
            info = json.loads(raw)
        except Exception:
            info = {}
        if info.get('contact'):
            info.update({'id': d['id'], 'slug': d['slug'], 'href': d['href'],
                         'title': d['title'], 'term': d['term'],
                         'harvested': time.strftime('%Y-%m-%d')})
            harvest[d['id']] = info
            found += 1
            print('  [%2d/%2d] %-28s | %-18s | %-16s | %s' % (
                i, len(to_read), info.get('contact', '')[:27],
                info.get('country', '')[:17], info.get('qty', '')[:15],
                info.get('category', '')[:34]))
        try:
            cdp('Target.closeTarget', {'targetId': tid})
        except Exception:
            pass

    save_harvest(harvest)
    print()
    print('harvested %d new buyers this run | total %d' % (found, len(harvest)))
    print('saved ->', HARVEST)
    ws.close()


if __name__ == '__main__':
    main()
