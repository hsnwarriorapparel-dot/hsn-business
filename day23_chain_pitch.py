#!/usr/bin/env python3
"""Chain / franchise corporate pitch engine for HSN Warrior Apparels.

WHY THIS EXISTS (2026-11-06): the tracker holds 13 TITLE Boxing Club rows
(emailing each location as if it were an independent gym), 21 Brooklyn
Fitboxing rows, 10 Victory Martial Arts rows and 3 UFC Gym rows. TITLE alone
runs 146 locations. Pitching a franchise ONE location at a time means:
  - the decision maker (a corporate/franchise buyer) never sees us
  - each location gets a separate, irrelevant, low-value email
  - we burn the 100/day quota on 100 tiny orders instead of a few large ones

One corporate email to the right address can win ALL locations.

This engine finds brand groups in the tracker (same brand across many
locations), locates a CENTRAL contact for the brand, and drafts one
corporate pitch per brand. It is DRAFT-ONLY by default: existing brand
relationships and any brand with a reply are never auto-sent.

Usage:
  day23_chain_pitch.py                # build + save drafts (no send)
  day23_chain_pitch.py --send         # send the drafts (only if --send given)
"""
import sys, os, re, csv, json, argparse, tempfile, time
sys.path.insert(0, '/home/ubuntu')

CSV = '/home/ubuntu/leads.csv'
OUT = '/home/ubuntu/day23_chain_pitches.json'
LOG = '/home/ubuntu/day23_chain_pitch_log.txt'

ap = argparse.ArgumentParser()
ap.add_argument('--send', action='store_true')
ap.add_argument('--min-locations', type=int, default=3)
args = ap.parse_args()

# Brands where a CENTRAL/corporate pitch makes sense. Each entry:
#   key -> (display name, central contact email, evidence, locations seen)
BRANDS = {
    'titleboxingclub.com': {
        'name': 'TITLE Boxing Club',
        'email': 'info@titleboxingclub.com',
        'evidence': '146 franchised locations (craft.co company profile); 13 tracked locations',
        'note': 'Independently owned and operated franchised locations, HQ Overland Park KS. '
                'A central supply agreement covers every location at once.',
    },
    'brooklynfitboxing.com': {
        'name': 'Brooklyn Fitboxing',
        'email': 'hello@brooklynfitboxing.com',
        'evidence': '21 tracked locations',
        'note': 'Boutique boxing fitness brand with a large location footprint.',
    },
    'victoryma.com': {
        'name': 'Victory Martial Arts',
        'email': 'summerlin@victoryma.com',   # no central address published; best tracked location GM
        'evidence': '10 tracked locations',
        'note': 'Multi-location martial arts franchise.',
    },
    'ufcgym.com': {
        'name': 'UFC Gym',
        'email': 'contact@ufcgym.com',
        'evidence': '3 tracked locations; contact@ufcgym.com found on the live site',
        'note': 'Franchised UFC Gym network.',
    },
    'moralesbox.com': {
        'name': 'Morales Box',
        'email': 'info@moralesbox.com',
        'evidence': '5 tracked locations; central address found on moralesbox.com',
        'note': 'Spanish boxing gym chain, multiple Bilbao locations.',
    },
    'rumbleboxinggym.com': {
        'name': 'Rumble Boxing',
        'email': 'tempe@rumbleboxinggym.com',   # no central address published; best tracked location
        'evidence': '6 tracked locations',
        'note': 'Boxing fitness brand with multiple gyms.',
    },
    'rockboxfitness.com': {
        'name': 'RockBox Fitness',
        'email': 'university@rockboxfitness.com',   # no central address published; best tracked location
        'evidence': '5 tracked locations',
        'note': 'RockBox Fitness brand, multiple sites.',
    },
    'jabzboxing.com': {
        'name': 'Jabz Boxing',
        'email': 'nphoenix@jabzboxing.com',   # no central address published; best tracked location
        'evidence': '3 tracked locations',
        'note': 'Jabz Boxing brand, multiple locations.',
    },
}

REGIONS = {
    'titleboxingclub.com': 'the United States',
    'brooklynfitboxing.com': 'Europe',
    'victoryma.com': 'the United States',
    'ufcgym.com': 'the United States',
    'moralesbox.com': 'Europe',
    'rumbleboxinggym.com': 'the United States',
    'rockboxfitness.com': 'the United States',
    'jabzboxing.com': 'the United States',
}

SUBJECT = ("{brand} - custom club equipment for {n} locations ({company})")


def body_for(brand_key, b, n_locations):
    region = REGIONS.get(brand_key, 'your market')
    return f"""{b['name']} team,

We work with multi-location boxing and martial arts brands, and {b['note']}

We have {b['evidence']}. Rather than pricing location by location, one supply
setup can cover them all: your logo and colours on every item, one order
consolidated for the whole network, and each location billed to its own cost
centre if that is how you run it.

Prices are the same for every location:

- Jiu-Jitsu Gi (450g): EUR 29.60
- Rash Guard: EUR 9.50
- MMA Shorts: EUR 9.90
- MMA Tights: EUR 12.50
- Jiu-Jitsu Belt: EUR 3
- Boxing Gloves (cowhide): EUR 25.50
- Shin Guards (cowhide): EUR 28.50
- Boxing Headgear (cowhide): EUR 24
- Hoodie: EUR 14.50

Minimum is 30 units per style, so a single location can test a style before
the whole network commits. We build a mockup with your logo and colours first,
and we handle shipping and customs so the total that lands has no added fees.

Which style would you want to see first, and how many locations would be in
the first run?

Best regards,
HSN Warrior Apparels
hsnwarriorapparel@gmail.com
+92 337 3336381"""


def load_rows():
    with open(CSV, newline='', encoding='utf-8-sig') as f:
        return list(csv.reader(f))


def day_tag():
    """The day tag comes from the newest dayNN_quota_state.json on disk."""
    import glob
    states = sorted(glob.glob('/home/ubuntu/day*_quota_state.json'))
    for s in reversed(states):
        try:
            d = json.load(open(s)).get('date')
            if d:
                return 'Daily ' + str(d)
        except Exception:
            continue
    return 'Daily ' + time.strftime('%Y-%m-%d', time.gmtime())


def mark_sent(brand, to, subject):
    """Record the corporate pitch on every tracked location of the brand, so
    the tracker shows the corporate pitch landed instead of leaving those rows
    looking like they were never contacted at this level."""
    import tempfile
    rows = load_rows()
    hdr = rows[0]
    idx = {h: i for i, h in enumerate(hdr)}
    n = 0
    for r in rows[1:]:
        e = (r[idx['Email']] if idx['Email'] < len(r) else '') or ''
        if e.lower().endswith('@' + brand):
            cur = (r[idx['Status']] if idx['Status'] < len(r) else '') or ''
            marker = 'chain pitch sent (%s, corporate)' % day_tag()
            if marker not in cur:
                r[idx['Status']] = (cur.rstrip(' |') + ' | ' + marker)[:250]
                n += 1
    if n:
        fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
        with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerows(rows)
        os.replace(tmp, CSV)
    return n


def main():
    rows = load_rows()
    hdr = rows[0]
    idx = {h: i for i, h in enumerate(hdr)}

    # count locations per brand from the tracker
    counts = {}
    for r in rows[1:]:
        e = (r[idx['Email']] if idx['Email'] < len(r) else '') or ''
        dom = e.lower().split('@')[-1]
        if dom in BRANDS:
            counts.setdefault(dom, []).append(r)

    pitches = []
    log_lines = []
    for key, b in BRANDS.items():
        hits = counts.get(key, [])
        if len(hits) < args.min_locations:
            log_lines.append(f"SKIP {b['name']}: only {len(hits)} tracked locations")
            continue
        # a brand with a live reply or HOT lead is a relationship - never
        # auto-send a corporate pitch over the top of it.
        replied = any(re.search(r'replied|reply from|interested|HOT LEAD', r[idx['Status']] or '', re.I) for r in hits)
        names = sorted(set((r[idx['Name']] or '').strip() for r in hits))
        p = {
            'brand': b['name'],
            'brand_key': key,
            'to': b['email'],
            'subject': SUBJECT.format(brand=b['name'], n=len(hits), company='HSN Warrior Apparels'),
            'body': body_for(key, b, len(hits)),
            'locations_tracked': len(hits),
            'evidence': b['evidence'],
            'location_names': names[:8],
            'has_reply': bool(replied),
            'auto_send': (not replied),
            'status': 'DRAFT-ONLY (brand has a reply)' if replied else 'READY',
        }
        pitches.append(p)
        log_lines.append(f"{b['name']:<24} locs={len(hits):<3} -> {b['email']:<34} {p['status']}")

    print('=== CHAIN / FRANCHISE CORPORATE PITCHES ===')
    for l in log_lines:
        print(' ', l)
    print()
    print(f'total brands: {len(pitches)}  |  ready to send: {sum(1 for p in pitches if p["auto_send"])}')

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(pitches, f, indent=2, ensure_ascii=False)
    print('saved ->', OUT)

    with open(LOG, 'a') as f:
        f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ' chain pitch build\n')
        for l in log_lines:
            f.write('  ' + l + '\n')

    if args.send:
        ready = [p for p in pitches if p['auto_send']]
        if not ready:
            print('nothing ready to send')
            return
        from outreach import gmail_send
        sent = 0
        for i, p in enumerate(ready, 1):
            print(f"  [{i}/{len(ready)}] {p['brand']} -> {p['to']}")
            res = gmail_send(p['to'], p['subject'], p['body'])
            print('      ', res)
            if res == 'sent':
                sent += 1
                p['status'] = 'SENT'
                marked = mark_sent(p['brand_key'], p['to'], p['subject'])
                print(f'       marked {marked} location rows')
                time.sleep(40)
            else:
                p['status'] = 'FAILED: %s' % res
        with open(OUT, 'w', encoding='utf-8') as f:
            json.dump(pitches, f, indent=2, ensure_ascii=False)
        print(f'chain pitches sent: {sent}/{len(ready)}')


if __name__ == '__main__':
    main()
