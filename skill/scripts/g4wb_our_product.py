"""Classify a go4WorldBusiness buyer listing as OURS or NOT OURS.

THE RULE: the directory slug is unreliable. The `fight-gear` page lists
steel scrap and diesel; the `martial-arts-mats` page lists prayer mats,
car mats and bath mats; the `martial-arts-gloves` page lists medical and
latex gloves.

The buyer's OWN `Buyer Of X` phrase is the only trustworthy signal. It
is the FIRST segment of the listing's category line:

    "Buyer Of Mat | Floor Mats"        -> NOT ours
    "Buyer Of Martial Arts Goods..."   -> ours

Filtering on an exact whitelist against that phrase is what turns raw
harvest entries into a usable target list.

Usage:
    from g4wb_our_product import is_ours, first_interest

    if is_ours(listing['category'], listing.get('product', '')):
        ...

Or as a filter over a harvest json:
    python3 g4wb_our_product.py g4wb_buyer_harvest_dir.json
"""
import json
import re
import sys

# Exact `Buyer Of X` phrases that are our line. Anything else is another
# trade, even if it appears on one of our category pages.
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
    'boxing shorts', 'boxing robe', 'mouthguard', 'headgear',
    'head guard',
}

# Other trades that appear INSIDE our categories and must never be quoted.
# These are checked against the interest phrase AND the product, so a
# listing whose product mentions one of them is dropped even when its
# category looks right.
NOT_OURS = (
    'steel scrap', 'diesel', 'coking coal', 'refractory', 'fresh fruit',
    'printing paper', 'art paper', 'card paper', 'woodfree',
    'rubber chemical', 'adhesive tape', 'self adhesive', 'carpet',
    'non-woven', 'prayer mat', 'bath mat', 'car mat', 'door mat',
    'grass mat', 'medical glove', 'latex glove', 'nitrile',
    'disposable glove', 'examination glove', 'scrub suit', 'hospital staff',
    'nursing', 'military', 'police', 'camouflage', 'work wear',
    'football team', 'football uniform', 'commercial uniform',
    'biker jacket', 'bomber jacket', 'leather jacket', 'fashion wear',
    'industrial glove', 'safety glove', 'hand safety',
)

# Product words that are ours even when the category phrase is vague.
# 'gi' alone is NOT here - it matches 'engine', 'gift', 'digit'.
OUR_PRODUCTS = (
    'karate gi', 'dobok', 'judo gi', 'bjj gi', 'kimono', 'rashguard',
    'rash guard', 'spats', 'boxing gloves', 'boxing glove', 'taekwondo belt',
    'karate belt', 'judo belt', 'mouth guard', 'mouthguard', 'head guard',
    'headgear', 'shin guard', 'shinguard', 'hand wrap', 'handwrap',
    'sparring', 'focus mitt', 'thai pad', 'kick pad',
)


def first_interest(category):
    """The buyer's own `Buyer Of X` phrase - the FIRST segment.

    The category line is 'Buyer Of A | B | C'. The first segment is what
    the buyer calls their business; the rest are sub-categories.
    """
    s = (category or '').split('|')[0].strip()
    if s.lower().startswith('buyer of'):
        s = s[9:].strip()
    return s


def is_ours(category, product=''):
    """True when this listing is genuinely in our product space."""
    interest = first_interest(category).lower()
    prod = (product or '').lower()
    blob = interest + ' || ' + prod
    # wrong trades win over everything - reject first
    if any(b in blob for b in NOT_OURS):
        return False
    if interest in OURS_EXACT:
        return True
    return any(p in prod for p in OUR_PRODUCTS)


def filter_records(records):
    """records: iterable of dicts with 'category' and optional 'product'."""
    return [r for r in records
            if is_ours(r.get('category', ''), r.get('product', ''))]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    data = json.load(open(sys.argv[1]))
    records = list(data.values()) if isinstance(data, dict) else data
    ours = filter_records(records)
    print('%d records -> %d in our product space' % (len(records), len(ours)))
    counts = {}
    for r in ours:
        k = first_interest(r.get('category', ''))
        counts[k] = counts.get(k, 0) + 1
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print('  %4d  %s' % (v, k))
    return 0


if __name__ == '__main__':
    sys.exit(main())
