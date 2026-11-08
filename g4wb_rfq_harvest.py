"""Harvest go4WorldBusiness BUY REQUIREMENTS with their full specifications.

The pages at /buyers/<country>/<category> are NOT a company directory.
Each block is a LIVE BUY REQUIREMENT posted by a buyer, and it carries:

    Product Name: Judo Belts
    Specifications: With Own Logo Following Colors: White/Yellow; ...
    Quantity Required : 100 Piece/Pieces
    Shipping Terms : CIF
    Destination Port : Portugal
    Payment Terms : LC
    Contact : Pedro Bernardo
    Buyer Of Martial Arts Belts

That is a far better signal than a contact name: it states WHAT they want,
HOW MANY, WHERE it ships and HOW they pay. A contact name alone is
unsearchable - searching "Pedro Bernardo" finds other people (people-search
sites, TikTok, BJJ profiles), which is why the company funnel outperforms
the person funnel 12x.

This module harvests the requirement itself and pairs it with the contact,
so the outreach can quote the actual spec and the actual terms.

Usage:
    python3 g4wb_rfq_harvest.py --pages 3 --countries oman portugal \
        --cats martial-arts-belts boxing-gloves
"""
import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, '/home/ubuntu')
import company_reach as cr

OUT = '/home/ubuntu/g4wb_rfq_harvest.json'

# What we manufacture.
OURS = re.compile(
    r'(martial art|judo|karate|taekwondo|bjj|brave ?jitsu|boxing|'
    r'kickbox|mma|mixed martial|fight ?wear|combat sport|'
    r'self[- ]defen[cs]e|dobok|'
    r'institutional uniform|school uniform|corporate uniform|dress uniform|'
    r'uniform fabric|cotton fabric|polyester fabric|poly viscose|'
    r'sport ?wear|sports ?goods|sports ?apparel|sports ?items?|'
    r'sport equipment|protective|gym wear|training gear|fight gear|'
    r'headgear|head guard|shin guard|mouth guard|hand wrap|'
    r'rank belt|judo belt|karate belt|taekwondo belt|'
    r'sports bag|gym bag|duffel|backpack)', re.I)

# Adjacent products that came through as 'ours' because 'mats' matched.
NOT_OUR_MATS = re.compile(
    r'(bath mat|carpet|floor mat|doormat|door mat|art paper|paper|'
    r'packaging mat|industrial mat|evening mat|seagrass|coir|'
    r'plastic mat|rubber scrap)', re.I)

# We are a MANUFACTURER of apparel and protective gear for sport. These
# are a different industry and must not be quoted:
#   PPE / medical / disposable      - PPE Kits, N95 masks, shoe covers
#   steel scrap, raw textile fabric  - Steel Scrap, RPET Polyester
#   badge holders, pins and ribbons   - ID Name Badge Holder
NOT_OUR_INDUSTRY = re.compile(
    r'(ppe\b|personal protective equipment|n95|face mask|shoe cover|'
    r'lab coat|disposable coverall|steel scrap|metal scrap|'
    r'rpet|raw material|textile fabric raw|crepe,|woven fabric|'
    r'badge holder|ribbon|lace|thread|pin\b|'
    r'disposable|surgical|hygiene)', re.I)

# Adjacent products that are a different industry entirely.
THEIRS = re.compile(
    r'(nitrile|latex|medical|surgical|chemical|safety glove|'
    r'work glove|cleaning|food grade|disposable|hi-vis|'
    r'supplement|creatine|protein|footwear|jogging shoe|gym shoe|'
    r'abaya|abayas|pump|motor|gear box|switch gear|carpet|spare part|'
    r'tyre|tire|oil|steel|cement|rice|flour|sugar|chicken|fish|'
    r'plastic|furniture|electrical|electronic|hardware|building|'
    r'real estate|paper|printing|solar|alarm|watch|glass|bottle|'
    r'seat belt|apron|goggle|helmet)', re.I)


def norm_qty(q):
    q = (q or '').strip()
    m = re.search(r'([\d,]{2,})', q)
    if m:
        try:
            return int(m.group(1).replace(',', ''))
        except ValueError:
            pass
    if 'container' in q.lower():
        return 20000
    return 0


# The page has TWO summaries per entry: a listing line and then the FULL
# requirement. Both are useful:
#
#   listing : Wanted : Martial Arts Belts Like Judo Belts
#             Buyer From Portugal | Quantity Required: 100 Pieces
#             Payment Terms: LC | Destination: Portugal
#
#   detail  : Product Name: Judo Belts
#             Specifications: With Own Logo Following Colors: ...
#             Quantity:100 pcs | Quantity Required : 100 Piece/Pieces
#             Shipping Terms : CIF | Destination Port : Portugal
#             Payment Terms : LC | Contact : Pedro Bernardo
#             Buyer Of Martial Arts Belts
#
# The detail block is the authoritative one. The listing line supplies the
# post date and the VERIFIED / ARCHIVED marker.
LISTING_RE = re.compile(
    r'(VERIFIED|ARCHIVED|NEW)?\s*([A-Z][a-z]{2}-\d{2}-\d{2})?\s*'
    r'Wanted\s*:\s*([^\n]{3,110}?)\s+Buyer From\s+([^\n]{2,40}?)\s+'
    r'Quantity Required\s*:\s*([^\n]{1,40}?)\s+Payment Terms\s*:\s*([^\n]{1,30}?)\s+'
    r'Destination\s*:\s*([^\n]{2,40}?)\s+Looking for suppliers from',
    re.I)


def parse_listing(block):
    """The compact listing line: date, status, title, country, qty, terms."""
    m = LISTING_RE.search(block)
    if not m:
        return {}
    return {
        'status': (m.group(1) or '').strip().upper(),
        'date': (m.group(2) or '').strip(),
        'title': (m.group(3) or '').strip(),
        'buyer_country': (m.group(4) or '').strip(),
        'list_qty': (m.group(5) or '').strip(),
        'list_payment': (m.group(6) or '').strip(),
        'list_destination': (m.group(7) or '').strip(),
    }


def parse_block(block):
    """Pull the requirement fields out of one directory block."""
    t = cr.strip_tags(block)
    out = parse_listing(t)

    # Product Name ends at the next label ('Specifications', 'Quantity', ...)
    m = re.search(r'Product Name\s*:\s*(.+?)(?=\bSpecifications\b|\bQuantity\b|'
                  r'\bShipping Terms\b|\bDestination Port\b|\bPayment Terms\b|'
                  r'\bContact\b|\bBuyer Of\b|\bLooking for suppliers\b)', t, re.I)
    if m:
        out['product'] = re.sub(r'\s+', ' ', m.group(1)).strip(' .;,')

    m = re.search(r'Specifications\s*:\s*(.+?)(?=\bQuantity\b|\bShipping Terms\b|'
                  r'\bDestination Port\b|\bPayment Terms\b|\bContact\b|'
                  r'\bBuyer Of\b|\bLooking for suppliers\b)', t, re.I)
    if m:
        out['specs'] = re.sub(r'\s+', ' ', m.group(1)).strip(' .;,')

    # 'Quantity Required : 100 Piece/Pieces' (detail) or the listing form
    m = re.search(r'Quantity Required\s*:\s*([^\n]{1,50}?)\s+(?=Shipping Terms|'
                  r'Destination Port|Payment Terms|Contact|Buyer Of|Looking for)',
                  t, re.I)
    if m:
        out['qty'] = m.group(1).strip()
    elif out.get('list_qty'):
        out['qty'] = out['list_qty']

    m = re.search(r'Shipping Terms\s*:\s*([^\n]{2,30}?)\s+(?=Destination Port|'
                  r'Payment Terms|Contact|Buyer Of|Looking for)', t, re.I)
    if m:
        out['shipping'] = m.group(1).strip()

    m = re.search(r'Destination Port\s*:\s*([^\n]{2,50}?)\s+(?=Payment Terms|'
                  r'Contact|Buyer Of|Looking for)', t, re.I)
    if m:
        out['destination'] = m.group(1).strip()
    elif out.get('list_destination'):
        out['destination'] = out['list_destination']

    m = re.search(r'Payment Terms\s*:\s*([^\n]{2,30}?)\s+(?=Contact|Buyer Of|'
                  r'Looking for|Destination)', t, re.I)
    if m:
        out['payment'] = m.group(1).strip()
    elif out.get('list_payment'):
        out['payment'] = out['list_payment']

    m = re.search(r'Contact\s*:\s*([^\n]{2,60}?)\s+(?=Buyer Of|Looking for|'
                  r'First page|Next)', t, re.I)
    if m:
        out['contact'] = m.group(1).strip()

    m = re.search(r'Buyer Of\s*(.+?)(?=\bFirst page\b|\bNext\b|'
                  r'\bDiscuss sourcing\b|$)', t, re.I)
    if m:
        out['buys'] = re.sub(r'\s+', ' ', m.group(1)).strip(' .;,')

    if not out.get('title'):
        m = re.search(r'Wanted\s*:\s*([^\n]{3,110})', t, re.I)
        if m:
            out['title'] = m.group(1).strip()
    return out


def ours_or_theirs(rec):
    text = ' '.join(str(rec.get(k, '')) for k in
                    ('product', 'specs', 'buys', 'category'))
    if NOT_OUR_MATS.search(text):
        return 'theirs'
    if NOT_OUR_INDUSTRY.search(text):
        return 'theirs'
    if THEIRS.search(text) and not OURS.search(text):
        return 'theirs'
    if OURS.search(text):
        return 'ours'
    return 'unknown'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pages', type=int, default=3)
    ap.add_argument('--countries', nargs='*', default=['oman', 'saudi-arabia'])
    ap.add_argument('--cats', nargs='*', default=['martial-arts-belts'])
    args = ap.parse_args()

    found = {}
    ours = {}
    theirs = {}
    unknown = {}
    for country in args.countries:
        for cat in args.cats:
            url = 'https://www.go4worldbusiness.com/buyers/%s/%s' % (country, cat)
            for page in range(1, args.pages + 1):
                purl = url if page == 1 else url + '?page=%d' % page
                html = cr.curl(purl, timeout=25)
                if not html:
                    # The site throttles a burst of requests and answers
                    # with a short stub. Back off HARD - 60s, then 120s.
                    print('  %-14s %-24s p%d  BLOCKED - backing off 60s'
                          % (country, cat[:23], page))
                    time.sleep(60)
                    html = cr.curl(purl, timeout=30)
                    if not html:
                        print('  %-14s %-24s p%d  still blocked - backing off 120s'
                              % (country, cat[:23], page))
                        time.sleep(120)
                        html = cr.curl(purl, timeout=30)
                if not html:
                    break
                # each requirement is a block; split on the 'Wanted :' marker
                # Each entry starts at 'Wanted :'. The detail block that
                # follows belongs to that entry, so split there and keep
                # each entry whole.
                page_text = cr.strip_tags(html)
                parts = re.split(r'(?=Wanted\s*:)', page_text)
                # The RAW html carries the inquiry route for each block:
                #   data-entity-id="1332643"
                #   href="/inquiries/send/buyleads/1332643/wanted-:-..."
                # Split the raw html the same way so the ids line up with
                # the text blocks.
                raw_parts = re.split(r'(?=Wanted\s*:)', html)
                added = 0
                for i, part in enumerate(parts):
                    if 'Buyer Of' not in part and 'Product Name' not in part:
                        continue
                    rec = parse_block(part)
                    # The listing header - 'VERIFIED Nov-03-26' - sits at the
                    # END of the PREVIOUS part, because the split happens at
                    # 'Wanted :'. Take the date and status from there.
                    if not rec.get('date') and i > 0:
                        prev = parts[i - 1]
                        pm = re.search(r'(VERIFIED|ARCHIVED|NEW)\s+([A-Z][a-z]{2}-\d{2}-\d{2})\s*$',
                                       prev.strip())
                        if pm:
                            rec['status'] = pm.group(1).upper()
                            rec['date'] = pm.group(2)
                    if not rec.get('product') and not rec.get('buys'):
                        continue
                    # Dedupe on the REQUIREMENT, not the category. The
                    # same requirement appears under several categories
                    # and on several pages.
                    key = '%s|%s|%s|%s' % (
                        (rec.get('product') or '').lower().strip()[:46],
                        (rec.get('contact') or '').lower().strip()[:26],
                        (rec.get('destination') or '').lower().strip()[:26],
                        (rec.get('qty') or '').lower().strip()[:24])
                    if key in found:
                        continue
                    found[key] = rec
                    rec['dir_country'] = country
                    rec['dir_category'] = cat
                    rec['url'] = purl
                    # the inquiry route for this exact requirement
                    if i < len(raw_parts):
                        rp = raw_parts[i]
                        im = re.search(r'href="(/inquiries/send/buyleads/(\d+)/[^"]*)"', rp)
                        if im:
                            rec['inquiry_href'] = im.group(1)
                            rec['buylead_id'] = im.group(2)
                    rec['qty_num'] = norm_qty(rec.get('qty'))
                    v = ours_or_theirs(rec)
                    rec['verdict'] = v
                    if v == 'ours':
                        ours[key] = rec
                    elif v == 'theirs':
                        theirs[key] = rec
                    else:
                        unknown[key] = rec
                    added += 1
                print('  %-14s %-24s p%d  blocks=%-3d ours=%-3d theirs=%-3d unknown=%d'
                      % (country, cat[:23], page, len(parts) - 1,
                         len(ours), len(theirs), len(unknown)))
                if added == 0:
                    break
                # Pace the fetches. The site answers a burst of requests
                # with a short rate-limit stub, and the whole harvest then
                # returns nothing.
                time.sleep(2.5)

    json.dump({'ours': ours, 'theirs': theirs, 'unknown': unknown},
              open(OUT, 'w'), indent=2, ensure_ascii=False)
    print()
    print('=== RFQ HARVEST ===')
    print('  OURS    : %d' % len(ours))
    print('  THEIRS  : %d' % len(theirs))
    print('  UNKNOWN : %d' % len(unknown))
    print()
    print('=== our requirements, biggest first ===')
    for k, r in sorted(ours.items(), key=lambda x: -x[1]['qty_num'])[:24]:
        print('  %-30s | %-16s | %-13s | %s' % (
            (r.get('product') or '')[:29], (r.get('qty') or '')[:15],
            (r.get('destination') or '')[:12], (r.get('payment') or '')[:10]))
    print()
    print('saved -> %s' % OUT)


if __name__ == '__main__':
    main()
