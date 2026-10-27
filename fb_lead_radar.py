#!/usr/bin/env python3
"""
FB Lead Radar — adapted from @itsliftmedia's Facebook client-finding method
for HSN Warrior Apparels. Runs BUYER-language Google searches against
facebook.com in the work browser, dumps ranked results to fb_leads.json.

Usage: python3 fb_lead_radar.py            (runs all queries, saves to fb_leads.json)
Output: /home/ubuntu/fb_leads.json + console summary.

Buyer language beats supplier language: "vendor recommendations", "where can I
get", "any recommendations", "supplier issue" — not "manufacturer offers".
"""
import sys, time, json, urllib.parse, os
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

OUT = '/home/ubuntu/fb_leads.json'

# Buyer-intent queries (tuned for martial arts gear, teams & clubs).
# qdr:m = last month only.
QUERIES = [
    'site:facebook.com "any recommendations" OR "vendor recommendations" "jiu jitsu gi" OR "bjj gi" club OR academy OR team',
    'site:facebook.com/groups "any recommendations" "mma shorts" OR "fight shorts" OR "rashguard" team OR club -jobs',
    'site:facebook.com "where can I get" custom "boxing gloves" OR "muay thai shorts" club OR gym',
    'site:facebook.com/groups "supplier" OR "vendor" "boxing gloves" OR "punch bags" club order OR bulk',
    'site:facebook.com "supplier issue" OR "need a new supplier" "fight shorts" OR "gis" OR "uniforms"',
]

BUYER_SIGNALS = ['recommendation', 'where can i', 'looking for', 'need a', 'supplier issue',
                  'anybody know', 'does anyone', 'who do you', 'best place', 'order custom']
SUPPLIER_NOISE = ['dm us', 'we manufacture', 'we are manufacturer', 'oem', 'wholesale available',
                  'our products', 'place your order', 'contact us for', 'get a quote']


def run():
    tabs = get_tabs()
    pages = [t for t in tabs if t.get('type') == 'page']
    if not pages:
        raise SystemExit('no browser page tabs')
    ws = connect(pages[0])
    cdp = make_cdp(ws)

    all_hits = []
    for q in QUERIES:
        url = ('https://www.google.com/search?q=' + urllib.parse.quote(q)
               + '&num=15&tbs=qdr:m')
        cdp('Page.navigate', {'url': url})
        time.sleep(7)
        res = js_eval(ws, """(() => {
          const items = [];
          document.querySelectorAll('div.g, .MjjYud').forEach(d => {
            const a = d.querySelector('a[href]');
            const h = d.querySelector('h3');
            const txt = (d.innerText || '').slice(0, 300);
            if (a && h) items.push({title: h.innerText.slice(0,120), url: a.href, txt});
          });
          return JSON.stringify(items.slice(0, 12));
        })()""")
        try:
            items = json.loads(res)
        except Exception:
            items = []
        for it in items:
            it['query'] = q
            low = (it['title'] + ' ' + it['txt']).lower()
            buyer = sum(1 for s in BUYER_SIGNALS if s in low)
            noise = sum(1 for s in SUPPLIER_NOISE if s in low)
            it['buyer_score'] = buyer - noise
            all_hits.append(it)
        time.sleep(2)

    # rank: buyer-intent first, dedupe by url
    seen, ranked = set(), []
    for it in sorted(all_hits, key=lambda x: -x['buyer_score']):
        if it['url'] in seen:
            continue
        seen.add(it['url'])
        ranked.append(it)

    with open(OUT, 'w') as f:
        json.dump({'generated': time.strftime('%Y-%m-%d %H:%M'), 'hits': ranked}, f, indent=1)

    strong = [h for h in ranked if h['buyer_score'] >= 2]
    print(f"total hits: {len(ranked)}, strong buyer-intent: {len(strong)}")
    for h in strong[:10]:
        print(f"  [{h['buyer_score']}] {h['title'][:80]}")
        print(f"        {h['url'][:100]}")
    print(f"saved -> {OUT}")
    ws.close()


if __name__ == '__main__':
    run()
