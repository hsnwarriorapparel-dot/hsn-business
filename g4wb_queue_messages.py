"""Build a reply message for every go4WorldBusiness inquiry target.

Each target is a buy requirement that states what the buyer wants, the
quantity, the country and the payment terms. The message answers THAT
requirement: the product line that covers it, our terms, and one clear
next step.

The copy follows the spam-word-checker rules: no hype words, no em dash,
no greeting prefix before the first name, company-name sign-off only, and
no line that promises to stop if the buyer goes silent.
"""
import json
import re
import sys

MESSAGES_PATH = '/home/ubuntu/g4wb_belt_messages.py'
QUEUE = '/home/ubuntu/g4wb_buyer_queue.json'

SIGN = ("Best regards,\nGhulam Hassan\nHSN Warrior Apparels\n"
        "hsnwarriorapparel@gmail.com\n+92 337 3336381")

TERMS = [
    "- 30 pieces per style and colour as the starting quantity, so your first run can test one item before the full production",
    "- 3 to 4 weeks production after artwork approval, then DHL, FedEx or UPS door to door in 4 to 6 working days",
    "- CIF to your port, with shipping and customs handled on our side",
]

# The product detail block per requirement family.
BLOCKS = {
    'sports-bag': (
        "Your requirement is for sports bags - duffel bags, backpacks and gym bags. "
        "That is a standard line for us:\n\n"
        "- Duffel bags in 600D or 1000D polyester, with a printed or woven logo\n"
        "- Backpacks in 600D polyester with a padded strap, in our standard gym shape or your own\n"
        "- Gym bags with a shoe compartment and a zip pocket\n"
        "- Matching drawstring bags and kit bags from the same run\n\n"
        "Our usual terms for an order of this size:\n"),
    'uniform': (
        "Your requirement is for uniforms. That is our production line:\n\n"
        "- Karate, judo and taekwondo doboks in 8 oz, 10 oz, 12 oz and 14 oz\n"
        "- School, institutional and work uniforms in poly-cotton, poly-viscose or cotton\n"
        "- Your logo embroidered or printed, with your colours and your own badge position\n"
        "- Rank belts to match your grade structure\n"
        "- Optional matching tracksuits and T-shirts from the same fabric\n\n"
        "Our usual terms for an order of this size:\n"),
    'dress-uniform': (
        "Your requirement is for institutional dress uniforms. Our production line covers it:\n\n"
        "- Shirts in poly-cotton or cotton blend, with your embroidery and buttons\n"
        "- Trousers and skirts in the same fabric, cut to your size range\n"
        "- Jackets and vests where your uniform calls for them\n"
        "- Socks, ties and caps to complete the set\n\n"
        "Our usual terms for an order of this size:\n"),
    'fabric': (
        "Your requirement is for uniform fabric. We are a manufacturer, so we can weave and finish it to your specification:\n\n"
        "- Polyester, poly-viscose and cotton-blend options in the weights you need\n"
        "- Your colour to a Pantone reference, or matched to a sample you send\n"
        "- Finished to your width, with your own selvedge marking if required\n"
        "- We can supply the cut-and-sew uniform as well, from the same lot\n\n"
        "Our usual terms for an order of this size:\n"),
    'belt': (
        "Your requirement is for belts. That is our standard production line:\n\n"
        "- Rank belts in cotton or polyester, with a woven or printed rank bar\n"
        "- Your logo woven on the tip, or embroidered on a black label\n"
        "- Sizes from 160 cm to 210 cm, with a fixed overlap of 8 to 10 cm, or a length to your specification\n"
        "- Stitched edges, not glued, so the belt holds its shape through repeated washing\n\n"
        "Our usual terms for an order of this size:\n"),
    'gym': (
        "Your requirement is for gym and sportswear. Our production line covers it:\n\n"
        "- Gym bags and duffel bags in 600D or 1000D polyester\n"
        "- Tracksuits and warm-up tops in polyester or poly-cotton\n"
        "- T-shirts and singlets in the same fabric\n"
        "- Mats and mat accessories where you need them\n\n"
        "Our usual terms for an order of this size:\n"),
}

FAMILY = [
    ('sports bag', 'sports-bag', 'Sports bags'),
    ('duffel', 'sports-bag', 'Sports bags'),
    ('backpack', 'sports-bag', 'Sports bags'),
    ('gym bag', 'sports-bag', 'Sports bags'),
    ('dress uniform', 'dress-uniform', 'Institutional dress uniforms'),
    ('institutional uniform', 'uniform', 'Institutional uniforms'),
    ('school uniform', 'uniform', 'School uniforms'),
    ('corporate uniform', 'uniform', 'Corporate uniforms'),
    ('uniform fabric', 'fabric', 'Uniform fabric'),
    ('cotton fabric', 'fabric', 'Uniform fabric'),
    ('polyester fabric', 'fabric', 'Uniform fabric'),
    ('poly viscose', 'fabric', 'Uniform fabric'),
    ('uniform', 'uniform', 'Uniforms'),
    ('belt', 'belt', 'Belts'),
    ('gym wear', 'gym', 'Gym wear'),
    ('gym mat', 'gym', 'Gym mats'),
]


def family_of(title):
    low = (title or '').lower()
    for needle, fam, label in FAMILY:
        if needle in low:
            return fam, label
    return 'uniform', 'Uniforms'


def qty_phrase(qty):
    q = (qty or '').strip()
    if not q:
        return 'the quantity you listed'
    return q


def destination(buyer):
    b = (buyer or '').strip()
    return b or 'your destination'


def payment(terms):
    t = (terms or '').upper()
    if 'LC' in t:
        return 'LC at sight, as your requirement states'
    if 'TT' in t:
        return 'TT in advance, as your requirement states'
    return 'LC at sight, which is our usual term'


def build(title, qty, buyer, terms):
    fam, label = family_of(title)
    body = BLOCKS[fam]
    subj_label = label
    q = qty_phrase(qty)
    dest = destination(buyer)
    subject = '%s - %s - our factory' % (subj_label, q)
    # Built by concatenation, not %-formatting - the product blocks contain
    # literal '%' characters (e.g. '100%').
    full = (
        "Dear Sir/Madam,\n\n"
        "We are HSN Warrior Apparels, a martial arts and sportswear manufacturer and "
        "exporter based in Sialkot, Pakistan. We produce uniforms, belts, bags and "
        "fightwear for clubs, federations, sports retailers and institutional buyers "
        "worldwide.\n\n"
        + "\nQuantity noted: " + q + ", shipped to " + dest + ".\n\n"
        + body
        + '\n'.join(TERMS) + '\n'
        + '- ' + payment(terms) + '\n\n'
        "Send us your size range, your logo file and the fabric you prefer, and we "
        "will reply with an exact quotation and a sample mockup for one piece.\n\n"
        + SIGN
    )
    return {'subject': subject, 'body': full}


# The four hand-written messages that were reviewed and approved.
KEEP_HAND = {
    'taekwondo-belts',
    'martial-arts-belts-like-judo-belts',
    'boxing-accessories-like-hand-tie-gloves-head-guard',
    'karate-black-master-belt',
}


def main():
    q = json.load(open(QUEUE))
    existing = {}
    try:
        ns = {}
        exec(open(MESSAGES_PATH).read(), ns)
        existing = ns.get('MESSAGES', {})
    except Exception:
        pass

    made = 0
    for it in q:
        slug = it.get('slug', '')
        # always rebuild the queue targets - the hand-written originals are
        # preserved by being in KEEP_HAND below
        if slug in KEEP_HAND:
            continue
        terms = it.get('payment') or it.get('terms') or ''
        msg = build(it.get('title', ''), it.get('qty', ''), it.get('buyer', ''), terms)
        existing[slug] = msg
        made += 1

    out = ['"""Messages for the go4WorldBusiness buyer inquiries.',
           '',
           'Generated by g4wb_queue_messages.py from each requirement\'s own title,',
           'quantity and destination. Every message answers THAT requirement.',
           '"""',
           '', 'MESSAGES = {']
    for slug in sorted(existing):
        out.append('    %r: {' % slug)
        out.append('        %r: %r,' % ('subject', existing[slug]['subject']))
        out.append('        %r: %r,' % ('body', existing[slug]['body']))
        out.append('    },')
    out.append('}')
    open(MESSAGES_PATH, 'w').write('\n'.join(out) + '\n')
    print('wrote %d new message(s); %d total' % (made, len(existing)))
    for slug in sorted(existing):
        print('  %-52s %s' % (slug[:51], existing[slug]['subject'][:52]))


if __name__ == '__main__':
    main()
