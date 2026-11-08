#!/usr/bin/env python3
"""Fetch the go4WorldBusiness /buyers/ pages that hold live requirements
in OUR product space, and extract the FULL detail of each one:

  - the listing header (VERIFIED / ARCHIVED + date)
  - the requirement title and the buyer's own 'Buyer Of ...' phrase
  - product name, specifications, HS code
  - quantity, shipping terms, destination port, payment terms
  - the inquiry route  /inquiries/send/buyleads/<id>/...

The deep harvest (g4wb_deep_harvest.py) only captured ONE field per
listing - the category and a single product. This one captures the whole
requirement, which is what a quote needs.

Pacing: the site throttles a burst of requests and answers with a ~2 KB
stub instead of the ~93 KB page. Because the stub is not empty, a naive
'if out.strip()' check accepts it and the harvest silently returns 0.
Requests are spaced and a short response is treated as a failure.
"""
import sys, os, re, json, time
sys.path.insert(0, '/home/ubuntu')
import company_reach as cr

OUT = '/home/ubuntu/g4wb_live_rfq.json'
BASE = 'https://www.go4worldbusiness.com/buyers'

# The listing header - 'VERIFIED Nov-03-26' - sits at the END of the
# PREVIOUS block, because the split happens at 'Wanted :'.
HDR_RE = re.compile(r'(VERIFIED|ARCHIVED|NEW)\s+([A-Z][a-z]{2}-\d{2}-\d{2})\s*$')
LIST_RE = re.compile(
    r'(VERIFIED|ARCHIVED|NEW)\s+([A-Z][a-z]{2}-\d{2}-\d{2})\s*'
    r'Wanted\s*:\s*([^\n]+?)\s*'
    r'Buyer From\s*([^\n|]+?)\s*\|?\s*'
    r'Quantity Required\s*:\s*([^\n|]+?)\s*\|?\s*'
    r'Payment Terms\s*:\s*([^\n|]+?)\s*\|?\s*'
    r'Quantity\s*:\s*([^\n|]+?)\s*\|?\s*'
    r'Shipping Terms\s*:\s*([^\n|]+?)\s*\|?\s*'
    r'Destination(?: Port)?\s*:\s*([^\n|]+?)\s*\|?\s*'
    r'Payment Terms\s*:\s*([^\n]+?)\s*$',
    re.M)

# The exact phrases that are our line. The page category is unreliable -
# 'fight-gear' pages list steel scrap - so the buyer's own 'Buyer Of X'
# phrase decides.
OURS_EXACT = {
    'uniforms', 'martial arts wear', 'martial arts goods and accessories',
    'boxing gloves', 'boxing head guards', 'boxing equipment',
    'boxing accessories', 'karate uniforms', 'karate gi', 'karate wear',
    'judo uniforms', 'judo wear', 'taekwondo uniforms', 'taekwondo wear',
    'taekwondo belts', 'martial arts belts', 'martial arts gloves',
    'martial arts mats', 'team uniforms', 'team wear', 'fight wear',
    'fight gear', 'fight shorts', 'mixed martial arts', 'mma wear',
    'mouth guards', 'head protection', 'head guards', 'shin guards',
    'hand wraps', 'kick pads', 'self defense', 'sports wear',
    'sportswear', 'sports clothing', 'sports garments', 'sports uniforms',
    'protective equipment', 'protective wear', 'gym wear', 'gym apparel',
    'fight shorts', 'boxing shorts', 'boxing robe', 'mouthguard',
    'headgear', 'head guard',
}

# Other trades that appear inside our categories and must never be quoted.
NOT_OURS = (
    'steel scrap', 'diesel', 'coking coal', 'refractory', 'fresh fruit',
    'printing paper', 'art paper', 'card paper', 'woodfree',
    'rubber chemical', 'adhesive tape', 'self adhesive', 'carpet',
    'non-woven', 'prayer mat', 'bath mat', 'car mat', 'door mat',
    'grass mat', 'medical glove', 'latex glove', 'nitrile',
    'disposable glove', 'examination glove', 'scrub suit', 'hospital staff',
    'nursing', 'military', 'police', 'camouflage', 'work wear',
    'football team', 'football uniform', 'commercial uniform',
)


def first_interest(category):
    """The buyer's own 'Buyer Of X' phrase - the first segment."""
    s = (category or '').split('|')[0].strip()
    if s.lower().startswith('buyer of'):
        s = s[9:].strip()
    return s


def is_ours(category, product):
    interest = first_interest(category).lower()
    prod = (product or '').lower()
    blob = interest + ' || ' + prod
    if any(b in blob for b in NOT_OURS):
        return False
    if interest in OURS_EXACT:
        return True
    for p in ('karate gi', 'dobok', 'judo gi', 'bjj gi', 'kimono',
              'rashguard', 'spats', 'boxing gloves', 'boxing glove',
              'taekwondo belt', 'karate belt', 'judo belt'):
        if p in prod:
            return True
    return False


def fetch_page(country, cat, tries=3):
    url = '%s/%s/%s' % (BASE, country, cat)
    for attempt in range(tries):
        html = cr.curl(url, timeout=30)
        # the throttled stub is short - treat it as a failure
        if html and len(html) > 8000:
            return html
        print('    %-18s %-26s p? short/failed (%d bytes) - retry %d'
              % (country, cat[:25], len(html or ''), attempt + 1))
        time.sleep(25 + attempt * 20)
    return None


def parse_page(html, country, cat):
    """Pull every requirement block out of one /buyers/ page."""
    text = cr.strip_tags(html)
    parts = re.split(r'(?=Wanted\s*:)', text)
    raw_parts = re.split(r'(?=Wanted\s*:)', html)
    out = []
    for i, part in enumerate(parts):
        if 'Buyer Of' not in part and 'Product Name' not in part:
            continue
        rec = {
            'dir_country': country,
            'dir_category': cat,
            'url': '%s/%s/%s' % (BASE, country, cat),
            'status': '', 'date': '',
        }
        # the listing header lives at the tail of the PREVIOUS block
        if i > 0:
            pm = HDR_RE.search(parts[i - 1].strip())
            if pm:
                rec['status'] = pm.group(1).upper()
                rec['date'] = pm.group(2)
        if not rec['date']:
            m = re.search(r'(VERIFIED|ARCHIVED|NEW)\s+([A-Z][a-z]{2}-\d{2}-\d{2})',
                          part)
            if m:
                rec['status'] = m.group(1).upper()
                rec['date'] = m.group(2)

        # the buyer's own interest phrase
        im = re.search(r'Buyer Of ([^\n|]+)', part)
        rec['interest'] = (im.group(1).strip() if im else '')[:120]
        # the requirement title
        tm = re.search(r'Wanted\s*:\s*([^\n]+)', part)
        rec['title'] = (tm.group(1).strip() if tm else '')[:160]
        # product name
        pm2 = re.search(r'Product Name\s*:\s*([^\n]+)', part)
        rec['product'] = (pm2.group(1).strip() if pm2 else rec['title'])[:160]
        # specifications
        sm = re.search(r'Specifications\s*:\s*([^\n]+)', part)
        rec['specs'] = (sm.group(1).strip() if sm else '')[:320]
        # Quantity / terms. The detail block is ONE long line, so a
        # greedy '[^\n|]+' swallows everything after the label. Stop at
        # the next known label instead.
        LABELS = ('Quantity Required', 'Quantity', 'Shipping Terms',
                  'Destination Port', 'Destination', 'Payment Terms',
                  'HS Code', 'Contact', 'Buyer Of', 'Product Name',
                  'Specifications', 'Wanted', 'Inquire Now',
                  'Add to Favorites', 'Looking for suppliers from',
                  'Inquire Now About Us')
        stop = '(?=' + '|'.join(re.escape(x) for x in LABELS) + r'\s*:|\|)'
        for label, key in (('Quantity Required', 'qty'),
                           ('Quantity', 'qty2'),
                           ('Shipping Terms', 'shipping'),
                           ('Destination Port', 'destination'),
                           ('Destination', 'destination'),
                           ('Payment Terms', 'payment'),
                           ('HS Code', 'hs_code'),
                           ('Contact', 'contact')):
            mm = re.search(label + r'\s*:\s*(.*?)' + stop, part)
            if mm and not rec.get(key):
                rec[key] = mm.group(1).strip(' \t|')[:90]
        # the inquiry route is in the RAW html
        if i < len(raw_parts):
            hm = re.search(r'href="(/inquiries/send/buyleads/(\d+)/[^"]*)"',
                           raw_parts[i])
            if hm:
                rec['inquiry_href'] = hm.group(1)
                rec['buylead_id'] = hm.group(2)
        # the full category phrase, for the interest check
        rec['category'] = rec['interest']
        rec['qty'] = rec.get('qty') or rec.get('qty2') or ''
        rec['dedupe'] = '%s|%s|%s' % (rec['title'].lower()[:40],
                                      country, rec['interest'].lower()[:40])
        if not is_ours(rec['category'], rec['product'] + ' ' + rec['title']):
            continue
        out.append(rec)
    return out


def main():
    # only the pages that actually hold a live requirement in our space
    PAGES = [
        ('oman', 'team-uniforms'), ('united-arab-emirates', 'team-uniforms'),
        ('saudi-arabia', 'team-uniforms'), ('australia', 'team-uniforms'),
        ('malaysia', 'team-uniforms'),
        ('united-arab-emirates', 'sports-goods-equipments'),
        ('egypt', 'martial-arts-gloves'), ('malaysia', 'martial-arts-belts'),
        ('portugal', 'martial-arts-gloves'), ('australia', 'fight-gear'),
        ('australia', 'mouth-guards'), ('israel', 'sports-goods-equipments'),
        # and the pages that hold the newest verified ones
        ('oman', 'uniforms'), ('united-arab-emirates', 'uniforms'),
        ('malaysia', 'uniforms'), ('saudi-arabia', 'uniforms'),
        ('egypt', 'uniforms'), ('portugal', 'uniforms'),
        ('oman', 'martial-arts-belts'), ('united-arab-emirates', 'martial-arts-belts'),
        ('oman', 'boxing-gloves'), ('united-arab-emirates', 'boxing-gloves'),
        ('oman', 'sportswear'), ('united-arab-emirates', 'sportswear'),
        ('saudi-arabia', 'sportswear'), ('australia', 'sportswear'),
        ('oman', 'karate-uniforms'), ('united-arab-emirates', 'karate-uniforms'),
        ('saudi-arabia', 'karate-uniforms'), ('malaysia', 'karate-uniforms'),
    ]
    only = set(sys.argv[1:2])
    all_recs = {}
    for country, cat in PAGES:
        if only and country not in only:
            continue
        html = fetch_page(country, cat)
        if not html:
            print('  %-18s %-26s BLOCKED' % (country, cat[:25]))
            continue
        recs = parse_page(html, country, cat)
        print('  %-18s %-26s %d ours' % (country, cat[:25], len(recs)))
        for r in recs:
            all_recs[r['dedupe']] = r
        time.sleep(2.5)
    json.dump(all_recs, open(OUT, 'w'), indent=2, ensure_ascii=False)
    live = [r for r in all_recs.values()
            if r.get('status', '').upper() != 'ARCHIVED'
            and r.get('date') and r.get('qty')]
    print()
    print('saved -> %s' % OUT)
    print('total in our space: %d | with a link: %d | live: %d'
          % (len(all_recs),
             sum(1 for r in all_recs.values() if r.get('inquiry_href')),
             len(live)))


if __name__ == '__main__':
    main()
