#!/usr/bin/env python3
"""Filter the raw g4WorldBusiness buyer harvest down to buyers whose OWN
category is in our product space.

The site's directory tags are loose - prayer mats and car mats land under
"martial-arts-mats", medical gloves under "boxing-gloves". So the filter uses
the buyer's own "Buyer Of ..." category, which is what they call themselves.
"""
import json
import re
import sys

# The two harvesters own separate files (they used to share one and wipe
# each other's entries). Merge them here.
RAW_FILES = ['/home/ubuntu/g4wb_buyer_harvest_dir.json',
             '/home/ubuntu/g4wb_buyer_harvest_search.json']
# kept for reading anything written before the split
LEGACY_RAW = '/home/ubuntu/g4wb_buyer_harvest.json'
OUT = '/home/ubuntu/g4wb_buyer_harvest_filtered.json'

OUR = re.compile(
    r'(martial art|karate|taekwondo|judo|boxing|fighter|fight ?(wear|gear|short|shorts|equipment)|'
    r'bjj|jiu[- ]?jitsu|mma|mixed martial|dobok|gym (wear|gloves|mats|equipment)|'
    r'yoga & gym|sports goods|sports apparel|sportswear|sports wear|sports equipment|'
    r'team uniform|uniform|headgear|head guard|shin guard|protective (gear|equipment)|'
    r'training gear|self defence|self defense|kickboxing|kick ?pad|muay thai|'
    r'boxing wear|mma wear|combat sport|fitness equipment & sports goods)', re.I)

# Names that are not real people/companies.
BAD_NAME = re.compile(r'^(purchaser|buyer|seller|admin|test|-|none|n/a|user|member|'
                       r'company|business|firm|trading|enterprise)$', re.I)


def load_raw():
    """Merge every harvest file into one dict, keyed uniquely."""
    merged = {}
    for f in RAW_FILES + [LEGACY_RAW]:
        try:
            d = json.load(open(f))
        except Exception:
            continue
        for k, v in d.items():
            # key on the content so the same buyer from two sources merges
            key = v.get('dedupe') or ('%s|%s|%s' % (
                str(v.get('contact') or '').lower(),
                (v.get('country') or '').lower(),
                str(v.get('product') or '').lower()))
            if key not in merged:
                merged[key] = v
    return merged


def main():
    raw = load_raw()
    if not raw:
        print('no harvest files yet')
        return
    keep = {}
    for k, v in raw.items():
        cat = str(v.get('category') or '')
        name = str(v.get('contact') or '').strip()
        if not name or BAD_NAME.match(name):
            continue
        if 'file a complaint' in cat.lower():
            continue
        if not OUR.search(cat):
            continue
        keep[k] = v
    json.dump(keep, open(OUT, 'w'), indent=2, ensure_ascii=False)
    print('harvested %d -> filtered %d buyers in our product space' % (len(raw), len(keep)))
    by = {}
    for v in keep.values():
        by[v.get('country') or v.get('dir_country') or '?'] = \
            by.get(v.get('country') or v.get('dir_country') or '?', 0) + 1
    print('  countries:', sorted(by.items(), key=lambda x: -x[1])[:10])
    for v in list(keep.values())[:12]:
        print('   %-24s | %-18s | %-34s | %s' % (
            str(v.get('contact'))[:23], (v.get('country') or '')[:17],
            str(v.get('category'))[:33], str(v.get('qty'))[:16]))


if __name__ == '__main__':
    main()
