#!/usr/bin/env python3
"""Turn harvested go4WorldBusiness buyer identities into real, contactable leads.

THE FUNNEL
----------
go4WorldBusiness buyer inquiry : 1 per day (JUNIOR). A hard slot.
This funnel                  : unlimited. The buyer NAME + COUNTRY + PRODUCT
                                CATEGORY from the public RFQ page is enough to
                                find the actual importing company on the open
                                web, then its email, then contact it directly.

So the 1/day platform slot is not the ceiling - it is one extra channel. This
script is that channel.

STEPS PER BUYER
  1. build a web-search query from name + country + category
  2. run it through the live search stack (DuckDuckGo html endpoint)
  3. find the company's own website
  4. pull candidate emails from the site + about/contact pages
  5. score them (role address on the company's own domain wins)
  6. write a leads.csv row, ready for the normal outreach wave

Run:  python3 buyer_reach.py            # process up to N unprocessed buyers
      python3 buyer_reach.py --limit 20
"""
import csv
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.parse

HARVEST = '/home/ubuntu/g4wb_buyer_harvest_filtered.json'

# Reuse the HARDENED verification from company_reach.py. This script had its
# own weaker copy and was adding junk: a sentry.wixpress.com error-tracker
# address, a beauty salon, a parked domain. One verified implementation is
# the only safe way to run two funnels.
from company_reach import (valid_email, NOT_A_COMPANY, OTHER_TRADE, OTHER_SPORTS,
                           PRODUCT_WORDS as CR_PRODUCT_WORDS, RETAIL_WORDS as CR_RETAIL,
                           WHOLESALE_WORDS, DEAD_SITE as CR_DEAD_SITE,
                           GOOD_ROLE, find_phones, site_domain as cr_domain,
                           strip_tags, title_hint)
LEDGER = '/home/ubuntu/send_ledger.jsonl'
# ---------------------------------------------------------------- RETIRED
# This script searches for the BUYER'S OWN NAME to find their company.
#
# It produced ZERO verified buyer companies and added junk: a privacy
# contact address, a Wix form address, a personal website. Searching a
# person's name finds OTHER people - people-search sites, TikTok, BJJ
# profiles.
#
# The company funnel does this work 12x better: 12 hits from 90 companies
# searched, against 0 from 25 people searched. The nightly pipeline calls
# company_reach.py instead (see .hermes/scripts/g4wb_dir_pipeline.sh).
#
# Kept for reference and for the shared leads.csv reader tests. Pass
# --force to run it anyway.
# -----------------------------------------------------------------------
if '--force' not in sys.argv:
    sys.stderr.write(
        'buyer_reach.py is RETIRED. It produced 0 verified buyer companies\n'
        'and added junk addresses. The company funnel does this work 12x\n'
        'better - see .hermes/scripts/g4wb_dir_pipeline.sh.\n'
        'Pass --force to run it anyway.\n')
    raise SystemExit(2)

CSV_PATH = '/home/ubuntu/leads.csv'
STATE = '/home/ubuntu/buyer_reach_state.json'

# Words that mean the company is NOT a buyer we want.
BAD_WORDS = re.compile(
    r'\b(indiaMART|alibaba|amazon|ebay|wikipedia|youtube|facebook|instagram|'
    r'linkedin|twitter|pinterest|reddit|glassdoor|indeed|zillow|'
    r'tradeindia|exportersindia|go4worldbusiness)\b', re.I)

# Generic / unusable mailbox names.
BAD_LOCAL = re.compile(
    r'^(no-reply|noreply|donotreply|postmaster|abuse|hostmaster|'
    r'webmaster|post|mail|email|info|admin|support|contact|hello|help|'
    r'enquiries|inquiry|sales|marketing|team|office|mailer|notification)@', re.I)

# Words that prove a site is in OUR product space. A buyer identity match
# alone is not enough - the site must actually be about what we make.
PRODUCT_WORDS = re.compile(
    r'(martial art|karate|taekwondo|judo|boxing|fighter|fight gear|fightwear|'
    r'bjj|jiu[- ]?jitsu|mma|mixed martial|boxing glove|headgear|head guard|'
    r'rash ?guard|fight short|gi uniform|dobok|sportswear|sports wear|'
    r'sports apparel|team uniform|kit[s]?\b|gym wear|self defence|self defense|'
    r'kickboxing|muay thai|kickboxing|kung fu|aikido|jeet kune do|'
    r'training gear|protective equipment|protective gear)', re.I)

# Parked / dead domains: the page title says the domain is for sale, or the
# body is a domain-marketplace placeholder. One match was cobrasports.com,
# a parked domain, whose page still contained the word 'sports'.
DEAD_SITE = re.compile(
    r'(for sale\s*[|·-]?\s*(buy this domain|domain for sale)|'
    r'domain (is )?for sale|this domain (is|may be) for sale|'
    r'domain names? for sale|buy this domain|inquire about this domain|'
    r'parked free|park your domain|domain parking)', re.I)

# A site selling to end customers is not a wholesale buyer.
RETAIL_WORDS = re.compile(
    r'(add to cart|checkout|my account|shopping cart|free shipping on orders|'
    r'add to wishlist|buy now|shop now|\$[0-9]+\.[0-9]{2}\s*USD|'
    r'wishlist|your cart|store locator|store hours|open now|'
    r'new and used|same item available in store)', re.I)

# Signs the site IS a business/import side.
WHOLESALE_WORDS = re.compile(
    r'(wholesale|bulk|oem|odm|distribut|import|export|supplier|b2b|'
    r'moq|minimum order|manufacturer|factory|sourcing|procurement|'
    r'contact us for pricing|request a quote|get a quote)', re.I)

# TLD -> country hint, used to sanity-check the buyer country vs the site.
SITE_COUNTRY_HINTS = {
    'my': 'malaysia', 'pt': 'portugal', 'om': 'oman', 'eg': 'egypt',
    'ae': 'united arab emirates', 'sa': 'saudi arabia', 'qa': 'qatar',
    'kw': 'kuwait', 'us': 'united states', 'uk': 'united kingdom',
    'de': 'germany', 'fr': 'france', 'es': 'spain', 'it': 'italy',
    'nl': 'netherlands', 'pl': 'poland', 'tr': 'turkey', 'br': 'brazil',
    'mx': 'mexico', 'ca': 'canada', 'au': 'australia', 'id': 'indonesia',
    'vn': 'vietnam', 'th': 'thailand', 'ph': 'philippines', 'ng': 'nigeria',
    'ke': 'kenya', 'gh': 'ghana', 'za': 'south africa', 'ru': 'russia',
    'ua': 'ukraine', 'jp': 'japan', 'kr': 'south korea', 'pk': 'pakistan',
}

# Roles we want for a first contact.
GOOD_ROLE = re.compile(r'^(sales|export|exports|info|contact|purchase|purchasing|'
                        r'orders|order|buy|buyer|import|imports|sourcing|'
                        r'business|commercial|marketing|md|owner|ceo|'
                        r'accounts|account|procurement)', re.I)

UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/156.0.0.0 Safari/537.36')


def load_json(path, default):
    try:
        return json.load(open(path))
    except Exception:
        return default


def curl(url, timeout=25):
    try:
        r = subprocess.run(
            ['curl', '-sL', '--max-time', str(timeout), '-A', UA,
             '-H', 'Accept-Language: en-US,en;q=0.9', url],
            capture_output=True, text=True, timeout=timeout + 8)
        return r.stdout or ''
    except Exception:
        return ''


def search(query):
    """Search via the REAL browser (Bing).

    Every curl-based search engine is blocked on this host: DuckDuckGo html
    returns 202 with zero results, Bing returns 200 with an empty body,
    Ecosia 403, Mojeek/Startpage/searx have no result markup. The work
    browser is real Chrome and renders results fine, so the search runs there.

    Bing wraps result links in bing.com/ck/a?... but each result carries a
    <cite> element with the REAL displayed url - that is what we take.
    """
    from browser_search import search as bsearch
    try:
        return bsearch(query)
    except Exception as e:
        print('    search error: %s' % str(e)[:90])
        return []


def candidate_emails(site):
    """Pull emails from a site and its contact/about pages."""
    found = {}
    pages = [site]
    home = curl(site, timeout=20)
    for m in re.finditer(r'href="([^"]*(?:contact|about|enquir|contact-us)[^"]*)"',
                         home, re.I):
        u = m.group(1)
        if u.startswith('/'):
            u = urllib.parse.urljoin(site, u)
        if u.startswith('http') and u not in pages:
            pages.append(u)
    for u in pages[:4]:
        html = home if u == site else curl(u, timeout=18)
        if not html:
            continue
        for m in re.finditer(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', html):
            e = m.group(0).lower()
            if not BAD_LOCAL.match(e) and 'example' not in e and valid_email(e):
                found[e] = found.get(e, 0) + 1
    return found


def site_domain(url):
    m = re.match(r'https?://([^/]+)', url)
    return m.group(1).lower() if m else ''


def process(buyer):
    """Find the real company + email for one harvested buyer."""
    name = buyer.get('contact', '').strip()
    country = buyer.get('country', '').strip()
    category = (buyer.get('category') or buyer.get('title') or '').strip()
    if not name:
        return None
    # "Mr. Aneez" -> "Aneez";  "Justin Leiva" -> "Justin Leiva"
    clean = re.sub(r'^(mr|mrs|ms|dr|prof)\.?\s+', '', name, flags=re.I).strip()
    parts = [p for p in clean.split() if len(p) > 1]
    if not parts:
        return None
    cat_kw = re.sub(r'\|.*$', '', category).strip()
    cat_kw = re.sub(r'^(Buyer Of|Buyer of)\s*', '', cat_kw, flags=re.I).strip()

    # Search strategies, best first. A person's name often does not appear on
    # their company's website, so the company-first queries matter most.
    queries = []
    if len(parts) >= 2:
        queries.append('"%s" %s' % (clean, country))
        queries.append('%s %s importer' % (cat_kw, country))
        queries.append('%s %s "%s" director' % (cat_kw, country, parts[-1]))
        queries.append('"%s %s" %s' % (parts[-1], parts[0], country))
    queries.append('%s %s supplier %s' % (cat_kw, country, 'wholesale'))
    queries.append('"%s" %s' % (clean, cat_kw))
    queries.append('%s %s distributor %s' % (cat_kw, country, cat_kw))

    seen_urls = []
    for q in queries:
        for href, title in search(q)[:8]:
            if BAD_WORDS.search(href) or BAD_WORDS.search(title):
                continue
            d = site_domain(href)
            if not d or d in seen_urls:
                continue
            if any(x in d for x in ('duckduckgo.com', 'google.com', 'bing.com')):
                continue
            if NOT_A_COMPANY.search(d):
                continue
            seen_urls.append(d)
            if not re.search(r'\.(com|net|org|io|co|ae|sa|pk|in|my|eg|pt|tr|my)\b', d):
                continue
            # VERIFY the site really is this buyer before taking its email.
            # A loose name search returns unrelated companies (a common first
            # name matches thousands of sites), so the site's own text must
            # contain the buyer's name AND a product word.
            page_html = home if False else curl(href, timeout=20)
            if not page_html:
                continue
            text = re.sub(r'<[^>]+>', ' ', page_html)
            text = re.sub(r'\s+', ' ', text)
            lowtxt = text.lower()
            name_tokens = [t for t in parts if len(t) > 2]
            name_ok = any(t.lower() in lowtxt for t in name_tokens)
            prod_ok = bool(PRODUCT_WORDS.search(text))
            if not (name_ok and prod_ok):
                continue
            # A parked domain or a "for sale" page is not a company.
            if DEAD_SITE.search(text) or DEAD_SITE.search(page_html):
                continue
            # A RETAIL STORE is not an importer. If the site sells to
            # end customers it is not a wholesale buyer - the first match
            # was an Arizona sporting-goods shop that had nothing to do with
            # the Malaysian buyer we were looking for.
            if RETAIL_WORDS.search(text) and not WHOLESALE_WORDS.search(text):
                continue
            # The site's own country should match the buyer's country, or the
            # site must at least be an importer/exporter page. A .com shop in
            # Arizona is not a Malaysian importer.
            site_loc = SITE_COUNTRY_HINTS.get(site_domain(href).split('.')[-1], '')
            buyer_c = (buyer.get('country') or '').strip().lower()
            if buyer_c and site_loc and site_loc != buyer_c:
                # only reject when the site clearly names a different country
                if not re.search(re.escape(buyer_c.split(',')[0]), lowtxt):
                    continue
            emails = candidate_emails(href)
            if not emails:
                continue
            # The email MUST be on the company's own domain. A random address
            # found in page text ('order@rand.org') is not this company, and a
            # sentry.wixpress.com address is an error tracker, not a mailbox.
            own = {}
            for e, score in emails.items():
                if not valid_email(e):
                    continue
                dom = e.split('@')[1]
                if dom == d or d.endswith(dom) or dom.endswith(d):
                    own[e] = score + (20 if GOOD_ROLE.match(e) else 8)
            if not own:
                continue
            best = None
            for e, score in own.items():
                if best is None or score > best[1]:
                    best = (e, score)
            if not best:
                continue
            # FINAL SELF-CHECK: re-fetch and confirm the site still shows our
            # product and is not a parked/dictionary/other-trade page.
            chk = curl(href, timeout=18)
            if not chk:
                continue
            ctext = strip_tags(chk)
            chead = (title_hint(chk) + ' ' + ctext[:900]).lower()
            if not CR_PRODUCT_WORDS.search(chead):
                continue
            if OTHER_TRADE.search(ctext[:1200]) or OTHER_SPORTS.search(chead):
                continue
            if CR_DEAD_SITE.search(chk) or NOT_A_COMPANY.search(d):
                continue
            return {'email': best[0], 'website': 'https://%s' % d,
                    'matched_name': clean, 'query': q}
    return None


LOCK = '/home/ubuntu/buyer_reach.lock'


def acquire_lock():
    """Exclusive lock on leads.csv - two reachers writing at once lost leads."""
    for _ in range(2):
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return True
        except FileExistsError:
            try:
                pid = int(open(LOCK).read().strip() or 0)
                os.kill(pid, 0)
                print('another buyer_reach is running (pid %d) - exiting' % pid)
                return False
            except (ProcessLookupError, ValueError):
                print('stale reach lock - reclaiming')
                try:
                    os.unlink(LOCK)
                except Exception:
                    pass
                continue
            except Exception:
                return False
    return False


def main():
    if not acquire_lock():
        return
    args = sys.argv[1:]
    limit = 20
    if '--limit' in args:
        limit = int(args[args.index('--limit') + 1])
    harvest = load_json(HARVEST, {})
    state = load_json(STATE, {'processed': {}})
    done = state.get('processed', {})
    # Key the state by the SAME key the filter uses. The filter merges the
    # harvest files and keys on name|country|product, so keying the state on
    # the harvest id made every buyer look unprocessed on every run.
    def state_key(v):
        return v.get('dedupe') or ('%s|%s|%s' % (
            str(v.get('contact') or '').lower(),
            (v.get('country') or '').lower(),
            str(v.get('product') or '').lower()))
    todo = []
    for k, b in harvest.items():
        sk = state_key(b)
        if sk in done:
            continue
        todo.append((sk, b))
    todo = todo[:limit]
    print('buyers harvested: %d | already processed: %d | to try: %d'
          % (len(harvest), len(done), len(todo)))
    if not todo:
        print('nothing new to work on')
        return

    # Load leads.csv for the FIELD LAYOUT only. The rows are appended at the
    # end through leads_safe_write.add_rows(), which re-reads the file at
    # write time - writing our whole in-memory copy back would destroy any
    # row the wave or the hunt added while we were working.
    with open(CSV_PATH, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))
    hdr = rows[0]
    idx = {h: i for i, h in enumerate(hdr)}
    maxid = max((int(r[0][1:]) for r in rows[1:] if r and r[0][1:].isdigit()), default=0)
    existing_emails = {(r[idx['Email']] or '').strip().lower()
                       for r in rows[1:] if len(r) > idx['Email']}
    new_rows = []          # rows to append safely at the end

    added = 0
    for i, (sk, b) in enumerate(todo, 1):
        print('[%d/%d] %s (%s) ...' % (i, len(todo), b.get('contact', '?'),
                                       b.get('country', '?')))
        try:
            hit = process(b)
        except Exception as e:
            print('    error: %s' % str(e)[:90])
            hit = None
        bid = b.get('id')
        if hit:
            email = hit['email']
            if email in existing_emails:
                print('    dup, already in tracker: %s' % email)
                done[sk] = {'status': 'duplicate', 'email': email}
            else:
                maxid += 1
                row = [''] * len(hdr)
                row[idx['Lead ID']] = 'L%d' % maxid
                row[idx['Name']] = hit['matched_name']
                row[idx['Type']] = 'Importer/Buyer (from go4WorldBusiness RFQ)'
                row[idx['Country']] = b.get('country', '')
                row[idx['Email']] = email
                row[idx['Website']] = hit['website']
                row[idx['Status']] = ('HUNTED (g4wb buyer identity %s): %s wants %s, %s. '
                                      'Reached directly - NOT via the platform inquiry form, '
                                      'so the 1/day platform limit does not apply.'
                                      % (time.strftime('%Y-%m-%d'), b.get('contact', ''),
                                         b.get('product') or b.get('title', '')[:40],
                                         b.get('qty', '')))
                row[idx['Profile Analysis']] = (
                    'Buyer identity harvested from the public go4WorldBusiness RFQ page: %s, %s. '
                    'Wanted: %s. Quantity: %s. Contact category: %s. '
                    'Found independently via web search -> %s -> email %s on the company own domain. '
                    'Payment/shipping terms from the RFQ: see the go4WorldBusiness page.'
                    % (b.get('contact', ''), b.get('country', ''),
                       b.get('product') or b.get('title', '')[:60], b.get('qty', ''),
                       b.get('category', '')[:80], hit['website'], email))
                row[idx['Notes']] = 'go4WorldBusiness RFQ buyer identity - ' + b.get('href', '')
                new_rows.append(row)
                existing_emails.add(email)
                added += 1
                print('    ADDED %s | %s | %s | %s' % (row[idx['Lead ID']],
                                                       hit['matched_name'],
                                                       email, hit['website']))
                done[sk] = {'status': 'added', 'email': email, 'lead': row[idx['Lead ID']]}
        else:
            print('    no match')
            done[sk] = {'status': 'no-match'}
        state['processed'] = done
        json.dump(state, open(STATE, 'w'), indent=2, ensure_ascii=False)

    # save - append safely so nothing written while we worked is lost
    from leads_safe_write import add_rows
    add_rows(new_rows)
    try:
        os.unlink(LOCK)
    except Exception:
        pass
    print()
    from leads_safe_write import read_rows as _live_rows
    print('added %d new contactable buyers | leads.csv now %d rows' % (added, len(_live_rows())))


if __name__ == '__main__':
    main()
