"""Merge the RFQ harvest with the buyer-company harvest.

Two harvests, two different views of the same buyers:

  g4wb_company_harvest.json  - WHO the buyer is
      company name, country, and the requirement they state in their
      go4WorldBusiness profile ('Buys police uniforms, uniforms.')

  g4wb_rfq_harvest.json       - WHAT they are buying right now
      the live buy requirement: product, quantity, destination, shipping
      and payment terms, dated and VERIFIED/ARCHIVED

Joining them on the requirement phrase gives one record with everything:

    company | contact | requirement | qty | destination | payment | date

The RFQ block carries a contact PERSON name and the company harvest
carries the COMPANY. The join key is the requirement phrase, which both
sides carry - the company profile says 'Buys police uniforms, uniforms.'
and the RFQ listing says 'Buyer Of Uniforms | ... Police Uniforms'.

The output is the queue for the inquiry engine: the platform inquiry goes
to a LIVE requirement (with a quantity and terms to answer), and the email
follow-up goes to the COMPANY (the only findable address).
"""
import json
import re
import sys

RFQ = '/home/ubuntu/g4wb_rfq_harvest.json'
COMPANY = '/home/ubuntu/g4wb_company_harvest.json'
OUT = '/home/ubuntu/g4wb_buyer_targets.json'

# Words that carry no meaning when comparing two requirement phrases.
STOP = set('''buys buyer of buying and with for the a an of or in on from to
legal entity inc llc ltd establishment established about contact required
quantity pieces piece pcs units unit quantity product name specifications
specification following colors colour colors payment terms shipping destination
port looking suppliers worldwide new verified archived'''.split())


def norm(s):
    return ' '.join(w for w in re.findall(r'[a-z0-9]+', (s or '').lower()) if w not in STOP)


def tokens(s):
    return set(norm(s).split())


def similar(a, b):
    """Two requirement phrases match when their content words overlap.

    The overlap must be in the DISTINCTIVE words. A requirement phrase
    like 'Steel Scrap' shares the word 'buys' and 'legal' with almost
    every record, and a loose match paired Steel Scrap with
    'Llc Company Eco-energy'. So the score is driven by the words that
    actually name a product - the ones that are NOT in every record.
    """
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    inter = ta & tb
    if not inter:
        return 0.0
    # every word here appears in most records, so it proves nothing
    GENERIC = {'uniform', 'uniforms', 'wear', 'product', 'products',
               'goods', 'accessories', 'garment', 'garments', 'clothing',
               'apparel', 'apparels', 'sports', 'sport', 'material',
               'materials', 'type', 'like', 'supplier', 'suppliers',
               'company', 'trading', 'establishment', 'established',
               'quantity', 'required', 'pieces', 'piece', 'units', 'unit',
               'payment', 'terms', 'shipping', 'destination', 'port',
               'looking', 'worldwide', 'new', 'verified', 'archived',
               'buys', 'buyer', 'legal', 'entity', 'contact', 'name',
               'specification', 'specifications', 'colors', 'colour',
               'following'}
    distinctive = inter - GENERIC
    if not distinctive:
        return 0.0
    # the distinctive words must cover a good share of the SHORTER side
    return len(distinctive) / float(min(len(ta - GENERIC) or ta,
                                        len(tb - GENERIC) or tb))


def main():
    rfq = json.load(open(RFQ))
    comp = json.load(open(COMPANY))
    ours_rfq = rfq.get('ours', {})
    companies = [v for v in comp.values() if v.get('company')]

    # index the companies by their stated requirement
    by_req = []
    for v in companies:
        b = v.get('_buys') or ''
        if not b:
            continue
        by_req.append((v, norm(b)))

    merged = []
    unmatched = []
    for key, r in ours_rfq.items():
        rtext = ' '.join(str(r.get(k, '')) for k in ('product', 'buys', 'specs'))
        best = None
        best_score = 0.0
        for v, cb in by_req:
            s = similar(rtext, cb)
            if s > best_score:
                best_score = s
                best = v
        rec = {
            'product': r.get('product', ''),
            'specs': r.get('specs', ''),
            'qty': r.get('qty', ''),
            'qty_num': r.get('qty_num', 0),
            'destination': r.get('destination', ''),
            'shipping': r.get('shipping', ''),
            'payment': r.get('payment', ''),
            'contact': r.get('contact', ''),
            'date': r.get('date', ''),
            'status': r.get('status', ''),
            'dir_country': r.get('dir_country', ''),
            'dir_category': r.get('dir_category', ''),
            'url': r.get('url', ''),
            'company': (best or {}).get('company', ''),
            'company_href': (best or {}).get('href', ''),
            'company_buys': (best or {}).get('_buys', ''),
            'match': round(best_score, 2),
        }
        if best_score >= 0.60 and rec['company']:
            merged.append(rec)
        else:
            unmatched.append(rec)

    # the same company can post several requirements - keep them all
    merged.sort(key=lambda r: (-r['qty_num'], r['company']))

    json.dump({'merged': merged, 'unmatched': unmatched},
              open(OUT, 'w'), indent=2, ensure_ascii=False)

    print('=== MERGE RESULT ===')
    print('  RFQ requirements (ours) : %d' % len(ours_rfq))
    print('  matched to a company     : %d' % len(merged))
    print('  no company found         : %d' % len(unmatched))
    print()
    print('=== the targets, biggest first ===')
    for r in merged[:30]:
        print('  %-30s | %-13s | %-15s | %-8s | %s' % (
            (r['company'] or '?')[:29], (r['qty'] or '')[:12],
            (r['destination'] or '')[:14], (r['payment'] or '')[:7],
            (r['product'] or '')[:34]))
    print()
    print('=== a full record ===')
    if merged:
        print(json.dumps(merged[0], indent=2, ensure_ascii=False))
    print('saved -> %s' % OUT)


if __name__ == '__main__':
    main()
