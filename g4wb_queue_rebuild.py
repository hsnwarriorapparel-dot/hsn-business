"""Rebuild the go4WorldBusiness inquiry queue from the LIVE buyleads.

The old queue was seeded from 8 hand-mapped targets, all ARCHIVED. There
are 23 live buyleads, 11 of them in our product space, most VERIFIED and
several posted in the last month.

The platform allows a JUNIOR member ONE buyer inquiry per day (Premium =
100/day). So the queue must hold the best ELIGIBLE target and send one per
day - and eligibility matters:
  - not PREMIUM MEMBERS ONLY (a JUNIOR account cannot send to those)
  - posted at least 5 days ago
  - not already sent

Ranking: a martial-arts/sports-apparel requirement first, then by how
fresh the requirement is, then by quantity.
"""
import json
import re
import sys
from datetime import datetime

sys.path.insert(0, '/home/ubuntu')

QUEUE = '/home/ubuntu/g4wb_buyer_queue.json'
LIVE = '/home/ubuntu/g4wb_buyleads_live.json'
RELEVANT = '/home/ubuntu/g4wb_buyleads_relevant.json'

# What we make.
OURS = re.compile(
    r'(institutional uniform|school uniform|corporate uniform|dress uniform|'
    r'martial arts? uniform|karate uniform|taekwondo|judo|boxing|'
    r'fight ?wear|gym wear|sports? bag|gym bag|duffel|backpack|'
    r'sports? mats?|gym mat|training wear|track ?suit|'
    r'uniform fabric|cotton fabric|polyester fabric|poly viscose|'
    r'hand ?tie|head ?guard|groin protector|belts?|dobok|'
    r'protective|sparring|team wear)', re.I)

# Adjacent but a different industry - not our order.
THEIRS = re.compile(
    r'(nitrile|latex|medical|surgical|chemical|safety glove|'
    r'work glove|cleaning|food grade|disposable|hi-vis|'
    r'supplement|creatine|protein|footwear|jogging shoes|gym shoes|'
    r'kid.?s wear|frock|housekeeping|towel)', re.I)

# How close is it to what we actually manufacture? Higher = better.
CORE = re.compile(
    r'(martial arts? uniform|karate uniform|taekwondo|judo|boxing|'
    r'fight ?wear|dobok|team wear|sports? bag|gym bag|duffel)', re.I)
GOOD = re.compile(
    r'(institutional uniform|school uniform|corporate uniform|dress uniform|'
    r'gym wear|sports? mats?|gym mat|training wear|track ?suit|'
    r'uniform fabric|cotton fabric|polyester fabric|poly viscose|'
    r'hand ?tie|head ?guard|groin protector|belts?)', re.I)


def age_days(datestr):
    """Days since a go4WorldBusiness date like 'Nov-03-26'."""
    if not datestr:
        return 999
    for fmt in ('%b-%d-%y', '%b-%d-%Y'):
        try:
            d = datetime.strptime(datestr.strip(), fmt)
            return (datetime.now() - d).days
        except ValueError:
            continue
    return 999


def to_number(d):
    """A rough quantity number so the biggest requirement ranks first."""
    if not d:
        return 0
    s = d.lower()
    if 'container' in s:
        return 20000
    if 'less than container' in s:
        return 18000
    m = re.search(r'([\d,]{2,})', s)
    if not m:
        return 100
    try:
        return int(m.group(1).replace(',', ''))
    except ValueError:
        return 100


def score(v):
    s = 0
    t = v.get('title', '')
    # UNIFORMS ARE THE PRIMARY PRODUCT. A 20ft container of school or
    # institutional uniforms is a far better order than gym bags, even
    # though bags are a bigger keyword match for our catalogue.
    if re.search(r'(institutional uniform|school uniform|corporate uniform|'
                 r'dress uniform|martial arts? uniform|karate uniform)', t, re.I):
        s += 140
    if re.search(r'uniform fabric|cotton fabric|polyester fabric|poly viscose', t, re.I):
        s += 90
    if CORE.search(t):
        s += 60
    if GOOD.search(t):
        s += 45
    # fresher is better, but not so fresh that it may still be a test post
    age = age_days(v.get('date'))
    if age <= 365:
        s += 30
    if age > 365 * 2:
        s -= 20
    s += min(40, to_number(v.get('qty')) // 500)
    return s


def main():
    rows = []
    for path in (LIVE, RELEVANT):
        try:
            data = json.load(open(path))
        except Exception:
            continue
        for v in data:
            if isinstance(v, dict) and v.get('href'):
                rows.append(v)
    seen = set()
    uniq = []
    for v in rows:
        h = v.get('href')
        if h in seen:
            continue
        seen.add(h)
        uniq.append(v)

    picked = []
    for v in uniq:
        t = v.get('title') or ''
        if not t:
            continue
        if THEIRS.search(t) and not OURS.search(t):
            continue
        if not OURS.search(t):
            continue
        raw = v.get('raw', '') or ''
        premium = 'PREMIUM MEMBERS ONLY' in raw
        picked.append({
            'slug': re.sub(r'[^a-z0-9]+', '-', t.lower())[:58],
            'href': v['href'],
            'qty': v.get('qty', ''),
            'buyer': (v.get('buyer') or '').replace('Buyer From', '').strip(),
            'date': v.get('date', ''),
            'status': 'VERIFIED' if 'VERIFIED' in raw else ('PREMIUM' if premium else 'NEW'),
            'premium': premium,
            'sent': False,
            'score': score(v),
            'title': t,
            'age_days': age_days(v.get('date')),
        })

    picked.sort(key=lambda i: -i['score'])
    json.dump(picked, open(QUEUE, 'w'), indent=2, ensure_ascii=False)

    print('=== inquiry queue rebuilt: %d targets ===' % len(picked))
    print('  (was 8, all ARCHIVED)')
    print()
    for i, it in enumerate(picked, 1):
        elig = []
        if it['premium']:
            elig.append('PREMIUM-ONLY (junior cannot)')
        if it['age_days'] < 5:
            elig.append('too new')
        print('  %2d. %-52s %-14s %-24s %s'
              % (i, it['title'][:51], it['buyer'][:13], it['qty'][:23],
                 ('; '.join(elig) or 'ELIGIBLE')))
    print()
    n = sum(1 for it in picked if not it['premium'] and it['age_days'] >= 5)
    print('%d of %d are eligible for a JUNIOR inquiry today' % (n, len(picked)))


if __name__ == '__main__':
    main()
