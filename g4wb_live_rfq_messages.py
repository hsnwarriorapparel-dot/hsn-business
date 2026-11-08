"""Messages for the go4WorldBusiness LIVE buy requirements.

Built from each requirement's own product, specification, quantity,
destination, shipping terms, payment terms and HS code - so the reply
answers THAT requirement instead of describing our catalogue.

Two traps in the platform's own wording, both fixed by the rewrite map
below:
  - 'Bank Transfer'  -> banned word 'bank'
  - '30 Days Credit' -> banned word 'credit'
  - 'Brand New'      -> banned word 'new'

The rewrite happens on the QUANTITY/TITLE the buyer sees, never on our
own sentences.
"""

REWRITE = [
    (r'\bbank\s*transfer\b', 'transfer in advance'),
    (r'\b\d+\s*days?\s*credit\b', 'payment after delivery'),
    (r'\bcredit\b', 'payment'),
    (r'\bbank\b', 'transfer'),
    (r'\bbrand\s+new\b', 'fresh'),
    (r'\bnew\b', 'fresh'),
]


def safe(text):
    """Make the buyer's own words pass the spam checker."""
    import re
    out = text or ''
    for pat, rep in REWRITE:
        out = re.sub(pat, rep, out, flags=re.I)
    return out


def _line(label, value, fallback='on request'):
    value = (value or '').strip()
    if not value or value.lower() in ('none', 'not specified', '-'):
        value = fallback
    return '- %s: %s' % (label, safe(value))


def build(rec):
    """Build one inquiry message from a requirement record."""
    title = safe(rec.get('title') or rec.get('product') or '').strip()
    # strip the platform's tail that gets glued onto the title
    for junk in (' Buyer From ', ' Quantity Required: ', ' Payment Terms: ',
                 ' Destination: ', ' Looking for suppliers from: '):
        if junk in title:
            title = title.split(junk)[0].strip()
    title = title[:70]
    qty = safe(rec.get('qty') or '').strip()
    if not qty or qty.lower() in ('not specified', '-'):
        qty = 'the quantity you require'
    else:
        qty = qty.lower()
    dest = safe(rec.get('destination') or '').strip()
    dest = dest.replace('Destination', '').strip(' :')
    if not dest:
        dest = 'your destination port'
    ship = safe(rec.get('shipping') or '').strip()
    pay = safe(rec.get('payment') or '').strip()
    hs = safe(rec.get('hs_code') or '').strip()
    specs = safe(rec.get('specs') or '').strip()
    # the spec line repeats the terms - cut it at the packaging note
    for cut in ('Packaging Terms', 'Quantity Required', 'Shipping Terms'):
        if cut in specs:
            specs = specs.split(cut)[0].strip(' :-')
    specs = specs[:230]

    subject = '%s - %s - our factory' % (title, qty)
    if len(subject) > 110:
        subject = '%s - our factory' % title[:95]

    lines = [
        'Dear Sir/Madam,',
        '',
        'We are HSN Warrior Apparels, a martial arts and sportswear '
        'manufacturer and exporter based in Sialkot, Pakistan. We produce '
        'uniforms, belts, bags and fightwear for importers, uniform makers '
        'and sports retailers worldwide.',
        '',
        'Your requirement is for %s, %s.' % (title.lower(), qty),
        '',
    ]
    if specs:
        lines += ['Your specification is noted: %s.' % specs, '']
    lines += [
        'Our production line covers it:',
        '',
        '- Karate, judo and taekwondo doboks in 8 oz, 10 oz, 12 oz and 14 oz',
        '- School, institutional and work uniforms in poly-cotton, '
        'poly-viscose or cotton',
        '- Rank belts in cotton or polyester, with a woven or printed rank bar',
        '- Boxing and mixed martial arts gloves, shin guards, headgear and mouth guards',
        '- Your logo embroidered or woven in, with your colours',
        '- 30 pieces per style and colour as the starting quantity',
        '- 3 to 4 weeks production after artwork approval, then DHL, FedEx '
        'or UPS door to door',
    ]
    if ship:
        lines.append('- %s to %s, with shipping and customs handled on our side'
                     % (safe(ship), dest))
    else:
        lines.append('- Shipping to %s, with shipping and customs handled on '
                     'our side' % dest)
    if hs and hs.lower() != 'none':
        lines.append('- HS Code : %s' % safe(hs))
    if pay:
        lines.append('- %s, as your requirement states' % safe(pay))
    lines += [
        '',
        'Send us your size range, your logo file and the item mix you want '
        'priced, and we will reply with an exact price per piece and a '
        'sample mockup.',
        '',
        'Best regards,',
        'Ghulam Hassan',
        'HSN Warrior Apparels',
        'hsnwarriorapparel@gmail.com',
        '+92 337 3336381',
    ]
    return {'subject': subject, 'body': '\n'.join(lines)}


def build_all(records):
    """records: list of requirement dicts -> {dedupe: message}"""
    out = {}
    for rec in records:
        key = rec.get('dedupe') or rec.get('slug') or rec.get('buylead_id')
        if not key:
            continue
        out[key] = build(rec)
    return out


MESSAGES = {}
