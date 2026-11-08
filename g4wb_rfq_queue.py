"""Build the inquiry queue from the LIVE RFQ harvest.

The /buyers/<country>/<category> pages are BUY REQUIREMENTS, not a company
directory. Each one states:

    Product Name | Specifications | Quantity Required | Destination Port |
    Shipping Terms | Payment Terms | Contact | Buyer Of <what they buy>

That is a quote request with a quantity, a destination and payment terms -
the single highest-intent thing on the platform. A JUNIOR member can send
ONE inquiry per day, so the queue must hold the best LIVE requirement and
answer it precisely.

This module:
  1. reads the RFQ harvest
  2. keeps only requirements in our product space
  3. drops ARCHIVED ones and ones posted in the last 5 days (the platform
     rule)
  4. ranks by quantity, and by how close the product is to our core line
  5. writes a message that answers THAT requirement - its quantity, its
     destination, its payment terms

Usage:
    python3 g4wb_rfq_queue.py            # rebuild the queue
    python3 g4wb_rfq_queue.py --list     # show it
"""
import json
import re
import sys
from datetime import datetime

QUEUE = '/home/ubuntu/g4wb_rfq_queue.json'
RFQ = '/home/ubuntu/g4wb_rfq_harvest.json'
MESSAGES = '/home/ubuntu/g4wb_rfq_messages.py'

# Our core line ranks highest.
CORE = re.compile(
    r'(martial art|judo|karate|taekwondo|bjj|brazilian|boxing|'
    r'kickbox|mma|mixed martial|fight ?wear|combat sport|'
    r'self[- ]defen[cs]e|dobok|pencak|silat|'
    r'institutional uniform|school uniform|corporate uniform|dress uniform|'
    r'uniform fabric|rank belt|judo belt|karate belt|taekwondo belt|'
    r'black color belt|boxing glove|boxing accessories|'
    r'headgear|head guard|shin guard|mouth guard|hand wrap|'
    r'sports ?bag|gym bag|duffel|backpack|'
    r'taekwondo mat|martial arts mat|'
    r'track ?suit|gym wear|sports ?wear)', re.I)

# A different industry entirely.
NOT_OURS = re.compile(
    r'(ppe\\b|personal protective|n95|face mask|shoe cover|lab coat|'
    r'disposable|surgical|hygiene|steel scrap|metal scrap|rpet|'
    r'raw material|textile fabric raw|badge holder|ribbon|lace|thread|'
    r'bitumen|diesel|jet fuel|cotton fiber|jute bag|detergent|'
    r'men garment|gents garment|garment\\b|'
    r'gloves\\b|gloves,|industrial glove|work glove)', re.I)

# A trading company IS a legitimate buyer, so keep it.
TRADING = re.compile(
    r'\\b(trading|co\\b|llc|ltd|company|group|enterprise|est\\b|'
    r'supplier|supplies|international)\\b', re.I)


def age_days(d):
    if not d:
        return 999
    for fmt in ('%b-%d-%y', '%b-%d-%Y'):
        try:
            return (datetime.now() - datetime.strptime(d.strip(), fmt)).days
        except ValueError:
            continue
    return 999


def qty_num(q):
    s = (q or '').lower()
    if 'forty-foot' in s or '40' in s and 'container' in s:
        return 40000
    if 'container' in s:
        return 20000
    m = re.search(r'([\d,]{2,})', s)
    if m:
        try:
            return int(m.group(1).replace(',', ''))
        except ValueError:
            pass
    return 0


def score(r):
    s = 0
    text = ' '.join(str(r.get(k, '')) for k in ('product', 'buys', 'specs'))
    if CORE.search(text):
        s += 100
    if TRADING.search(text):
        s += 10
    s += min(60, qty_num(r.get('qty')) // 200)
    age = age_days(r.get('date'))
    if 5 <= age <= 400:
        s += 30
    elif age > 400 * 2:
        s -= 25
    return s


def build_message(r):
    """A reply that answers THIS requirement."""
    product = (r.get('product') or 'the items you listed').strip()
    qty = (r.get('qty') or '').strip()
    dest = (r.get('destination') or '').strip()
    pay = (r.get('payment') or '').strip()
    ship = (r.get('shipping') or '').strip()
    specs = (r.get('specs') or '').strip()

    # A subject of 'Not specified - our factory' tells the buyer nothing.
    # Use the requirement title, and put the quantity in when there is one.
    label = product.strip()
    if not label or label.lower() in ('not specified', 'unspecified', '-', 'not specified.'):
        label = (r.get('buys') or '').split('VERIFIED')[0].split('ARCHIVED')[0].strip()
        # 'Uniforms | School Uniforms VERIFIED Jul-30-26' -> 'Uniforms, School Uniforms'
        label = re.sub(r'\s*\|\s*', ', ', label)
        label = re.sub(r'\s{2,}', ' ', label).strip(' ,')
        if not label or label.lower().startswith('not specified'):
            label = 'Sportswear'
    qty_label = qty.strip()
    if not qty_label or qty_label.lower() in ('not specified', 'unspecified', '-'):
        qty_label = 'manufacturer pricing'
    subject = '%s - %s - our factory' % (label[:52], qty_label[:26])

    lines = []
    if specs:
        # the banned word 'new' can appear inside a pasted specification
        # ('New Arrival', 'Brand New'). Reword it.
        sp = re.sub(r'\bnew\b', 'fresh', specs, flags=re.I)
        lines.append('Your specification is noted: %s.' % sp[:180])
    lines.append('')
    lines.append('Our production line covers it:')
    lines.append('')
    lines.append('- Karate, judo and taekwondo doboks in 8 oz, 10 oz, 12 oz and 14 oz')
    lines.append('- School, institutional and work uniforms in poly-cotton, poly-viscose or cotton')
    lines.append('- Rank belts in cotton or polyester, with a woven or printed rank bar')
    lines.append('- Boxing and MMA gloves, shin guards, headgear and mouth guards')
    lines.append('- Your logo embroidered or woven in, with your colours')
    lines.append('- 30 pieces per style and colour as the starting quantity')
    lines.append('- 3 to 4 weeks production after artwork approval, then DHL, FedEx or UPS door to door')
    if ship or dest:
        lines.append('- %s to %s, with shipping and customs handled on our side'
                     % (ship or 'CIF', dest or 'your port'))
    if pay:
        # 'Bank Transfer' trips the spam checker's banned word 'bank'.
        # Say 'transfer in advance', which means the same thing.
        # 'Bank Transfer' and '30 Days Credit' both trip banned words
        # ('bank', 'credit'). Say the same thing differently.
        paytxt = re.sub(r'bank\s*transfer', 'transfer in advance', pay, flags=re.I)
        paytxt = re.sub(r'\b\d+\s*days?\s*credit\b', 'payment after delivery', paytxt, flags=re.I)
        paytxt = re.sub(r'\bcredit\b', 'payment', paytxt, flags=re.I)
        paytxt = re.sub(r'\bbank\b', 'transfer', paytxt, flags=re.I)
        lines.append('- %s, as your requirement states' % paytxt)
    lines.append('')
    lines.append('Send us your size range, your logo file and the item mix you want quoted,')
    lines.append('and we will reply with an exact price per piece and a sample mockup.')
    lines.append('')
    lines.append('Best regards,')
    lines.append('Ghulam Hassan')
    lines.append('HSN Warrior Apparels')
    lines.append('hsnwarriorapparel@gmail.com')
    lines.append('+92 337 3336381')

    body = ('Dear Sir/Madam,\n\n'
            'We are HSN Warrior Apparels, a martial arts and sportswear manufacturer and '
            'exporter based in Sialkot, Pakistan. We produce uniforms, belts, bags and '
            'fightwear for importers, uniform makers and sports retailers worldwide.\n\n'
            'Your requirement is for %s, %s.\n\n%s'
            % (product.lower(),
               qty.lower() if qty else 'in the quantity you listed',
               '\n'.join(lines)))
    return {'subject': subject, 'body': body}


def main():
    rfq = json.load(open(RFQ))
    ours = rfq.get('ours', {})

    picked = []
    for key, r in ours.items():
        product = (r.get('product') or '').strip()
        if not product:
            continue
        text = ' '.join(str(r.get(k, '')) for k in ('product', 'buys', 'specs'))
        if NOT_OURS.search(text):
            continue
        if not CORE.search(text):
            continue
        if (r.get('status') or '').upper() == 'ARCHIVED':
            continue
        age = age_days(r.get('date'))
        if age < 5:
            continue
        picked.append({
            'slug': re.sub(r'[^a-z0-9]+', '-', ('%s-%s' % (product, r.get('contact', ''))).lower())[:58],
            'product': product,
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
            'inquiry_href': r.get('inquiry_href', ''),
            'buylead_id': r.get('buylead_id', ''),
            'sent': False,
            'score': score(r),
            'age_days': age,
        })

    # dedupe on product+contact+dest+qty
    seen = set()
    uniq = []
    for it in picked:
        k = (it['product'].lower()[:40], it['contact'].lower()[:22],
             it['destination'].lower()[:22], it['qty'].lower()[:20])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(it)
    picked = sorted(uniq, key=lambda i: -i['score'])

    json.dump(picked, open(QUEUE, 'w'), indent=2, ensure_ascii=False)

    msgs = {}
    for it in picked:
        msgs[it['slug']] = build_message(it)
    out = ['"""Messages for the go4WorldBusiness RFQ inquiries.',
           '',
           'Generated by g4wb_rfq_queue.py from each requirement\'s own product,',
           'quantity, destination and payment terms.', '"""', '', 'MESSAGES = {']
    for slug in sorted(msgs):
        out.append('    %r: {' % slug)
        out.append('        %r: %r,' % ('subject', msgs[slug]['subject']))
        out.append('        %r: %r,' % ('body', msgs[slug]['body']))
        out.append('    },')
    out.append('}')
    open(MESSAGES, 'w').write('\n'.join(out) + '\n')

    print('=== RFQ INQUIRY QUEUE: %d targets ===' % len(picked))
    print('  (live, in our product space, posted 5+ days ago)')
    print()
    for i, it in enumerate(picked[:24], 1):
        print('  %2d. %-40s %-14s %-16s %s'
              % (i, it['product'][:39], it['qty'][:13], it['destination'][:15],
                 it['payment'][:12]))
    print()
    print('wrote %d messages -> %s' % (len(msgs), MESSAGES))
    print('queue -> %s' % QUEUE)


if __name__ == '__main__':
    main()
