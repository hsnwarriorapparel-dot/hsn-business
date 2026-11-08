#!/usr/bin/env python3
"""Turn go4WorldBusiness buyer COMPANIES into contactable leads.

THE FUNNEL
----------
go4WorldBusiness lets a JUNIOR member send only ONE buyer inquiry per day.
That makes the platform's inquiry form a 1/day slot, not a channel.

The site's buyer directory publishes the BUYER COMPANIES themselves:
    /buyers/oman/sports-goods-equipments.html
        -> Al Ali Trading And Cont.
        -> Muscat Sports LLC
        -> Supa Sportsman LLC
A company name is a strong search key: the company has a website, and the
website has a sales email. We find the same buyer on the open web and contact
them directly - no platform limit, no captcha, no daily cap.

VERIFICATION (a wrong lead is worse than no lead)
  * the site must mention a product word from OUR space
  * the site must NOT be a parked/for-sale domain
  * the site must NOT be an end-customer retail store
  * the email must be on the company's OWN domain
  * the company name (or a distinctive token of it) must appear on the site

Run:  python3 company_reach.py --limit 25
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

HARVEST = '/home/ubuntu/g4wb_company_harvest.json'
CSV_PATH = '/home/ubuntu/leads.csv'
STATE = '/home/ubuntu/company_reach_state.json'

sys.path.insert(0, '/home/ubuntu')

# Products we make - a site must talk about one of these.
PRODUCT_WORDS = re.compile(
    r'(martial art|karate|taekwondo|judo|boxing|fighter|fight ?(gear|wear|short|shorts)|'
    r'bjj|jiu[- ]?jitsu|mma|mixed martial|dobok|gym (wear|gloves|mats|equipment|wear)|'
    r'yoga ?(mat|wear|pants)|sportswear|sports wear|sports apparel|sports goods|'
    r'sports equipment|sports ?items|team uniform|uniform|headgear|head guard|'
    r'shin guard|protective (gear|equipment)|training gear|self defence|self defense|'
    r'kickboxing|kick ?pad|muay thai|kung fu|aikido|boxing wear|mma wear|'
    r'combat sport|fitness equipment|sporting good|sport equipment|'
    r'sport goods|sports gear|t-shirt|polo shirt|'
    r'sports kit|custom kit|team kit|football kit|jersey)', re.I)

# Sports that are NOT our line. A golf results site ('golfscale.com' -
# "Bridging the worlds of Professional Golf") matched on 'sports equipment'.
OTHER_SPORTS = re.compile(
    r'(professional golf|golf tournament|golf results|golf leaderboard|'
    r'golf scores|golf course|golf club|golf swing|golfer|'
    r'cricket|football league|rugby|tennis|swimming|diving|surfing|'
    r'cycling|bike|skateboard|snowboard|skiing|fishing|hunting|'
    r'badminton|volleyball|table tennis|bowling)', re.I)

# A blog, a fighter-profile site or a magazine - not a buyer.
#   woc-org.com        -> "Boxing fighter profiles, comparisons, top athletes"
#   thekaratelifestyle.com -> "Martial Arts, Health & Spirituality" blog
INFO_SITE = re.compile(
    r'(fighter profiles?\b|player profiles?|athlete profiles?|'
    r'top athletes\b|rankings?\b|results? and statistics|'
    r'boxing news|martial arts blog|karate blog|training diary|'
    r'news and blog|blog posts?|latest articles|'
    r'about me\b|share this post|leave a comment|posted on|'
    r'terms? of karate\b|karate stances\b|learn japanese\b|'
    r'health & spirituality|martial arts, health|'
    r'encyclopedia|wiki(pedia)?\b)', re.I)

# A Cloudflare / bot-challenge wall. The page shows 'Attention Required!' or
# 'Just a moment...' but the rest of the HTML can still contain the real
# site's content - so the product/name checks pass while the phone comes
# from the challenge page. classicfootballshirts.com and galaxysports.com
# both did this. Treat the page as unusable.
CHALLENGE_WALL = re.compile(
    r'(attention required|just a moment|performing security verification|'
    r'checking your browser|enable javascript and cookies to continue|'
    r'__cf_chl|cf-browser-verification|ray id)', re.I)

# A WordPress/Elementor DEMO template. The stock filler is 'A small river
# named Duden flows by their place' (the classic Elementor lorem ipsum) and
# the contact block is a placeholder with a US +1 (859) number on a non-US
# domain. arapparels.pk was such a site - not a real company.
TEMPLATE_SITE = re.compile(
    r'(a small river named duden|flows by their place|'
    r'lorem ipsum dolor sit amet|consectetur adipiscing elit|'
    r'lorem ipsum|'
    r'\+1 \(859\)|'
    r'\[email\s*&#160;protected\]|\[email[^\]]*protected\]|'
    r'lorem-ipsum|placeholder\s*email)', re.I)

# Sites that are never a buying company. 'definitions.net' is a dictionary -
# it matched two Omani buyers because the word 'kit' appears in every
# dictionary entry.
NOT_A_COMPANY = re.compile(
    r'^(definitions\.net|definition\.net|wikipedia\.|wiktionary\.|'
    r'dictionary\.|thesaurus\.|quizlet\.|merriam-webster\.|'
    r'pinterest\.|facebook\.com|instagram\.com|twitter\.com|'
    r'youtube\.com|tiktok\.com|reddit\.com|quora\.com|medium\.com|'
    r'linkedin\.com|glassdoor\.com|indeed\.com|amazon\.|ebay\.|alibaba\.|'
    r'zoominfo\.com|rocketreach\.co|apollo\.io|signalhire\.com|'
    r'contactout\.com|b2bhint\.com|datanyze\.com|decypha\.com|'
    r'clarifiedby\.|digidna\.com|cybo\.com|info-clipper\.com|'
    r'craft\.co|godaddy\.com|wix\.com|squarespace\.com|weebly\.com|'
    r'blogspot\.|wordpress\.com|hubspot\.com|shopify\.com|'
    r'spokeo\.com|beenverified\.com|truepeoplesearch|radaris\.com|'
    r'clustrmaps\.com|fastpeoplesearch|radaris\.io|peoplefinder|'
    r'checkpeople|veripages\.com|pipl\.com|leadiq\.com|'
    r'dnb\.com|apollo\.io|zoominfo\.com|clearbit\.com|'
    # The STANDS4 network - 16+ reference/dictionary sites that all look
    # alike and all carry a shared contact phone. definitions.net was
    # accepted once (as 'Shuaib' and 'Ameer' in Oman) because only that
    # one domain was listed.
    r'abbreviations\.net|anagrams\.net|biographies\.net|'
    r'calculators\.net|convert\.net|grammar\.com|literature\.com|'
    r'lyrics\.net|phrases\.net|poetry\.net|quotes\.net|'
    r'references\.net|rhymes\.net|scripts\.net|symbols\.net|'
    r'synonyms\.net|uszip\.com|stands4\.com|webmaster\.net)', re.I)

# Gambling / betting sites are never buyers of our products. galaxysports.com
# is a sportsbook ("Galaxy Sportsbook's live betting software").
GAMBLING_SITE = re.compile(
    r'(sportsbook|sports betting|live betting|betting software|casino|'
    r'poker room|gambling|odds? betting|sports lottery|'
    r'place your bets|bet on all)', re.I)

# A site selling to end customers is not a wholesale buyer.
# End-customer retail -> not an importer.
RETAIL_WORDS = re.compile(
    r'(add to cart|add to wishlist|shopping cart|my account|checkout|'
    r'wishlist|store locator|store hours|open now|free shipping on orders|'
    r'buy now|shop now|same item available in store|new and used|'
    r'\\$[0-9]+\\.[0-9]{2}\\s*USD)', re.I)

# Business side - a plus, not a requirement.
WHOLESALE_WORDS = re.compile(
    r'(wholesale|bulk|oem|odm|distribut|import|export|supplier|b2b|'
    r'moq|minimum order|manufacturer|factory|sourcing|procurement|'
    r'contact us for pricing|request a quote|get a quote)', re.I)

# Parked / dead domain.
DEAD_SITE = re.compile(
    r'(for sale\s*[|·-]?\s*(buy this domain|domain for sale)|'
    r'domain (is )?for sale|this domain (is|may be) for sale|'
    r'domain names? for sale|buy this domain|inquire about this domain|'
    r'parked free|park your domain|domain parking)', re.I)

# Emails we will not contact.
BAD_LOCAL = re.compile(
    r'^(no-reply|noreply|donotreply|postmaster|abuse|hostmaster|'
    r'webmaster|post|mail|email|admin|support|help|help-euro|'
    r'no-reply|donotreply)@', re.I)

GOOD_ROLE = re.compile(r'^(sales|export|exports|info|contact|purchase|purchasing|'
                        r'orders|order|buy|buyer|import|imports|sourcing|'
                        r'business|commercial|md|owner|ceo|accounts|account|'
                        r'procurement|office|team)', re.I)

# A real email: a sensible local part on a real-looking domain. This rejects
# the junk that comes out of html: 'a-logo-black-@1x.png' (a filename),
# 'order@rand.org' (a random string in page text).
VALID_EMAIL = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._%+-]{1,63}@[A-Za-z0-9][A-Za-z0-9.-]{1,61}\.[A-Za-z]{2,24}$')
# TLDs that are never a real mail host.
JUNK_TLD = re.compile(r'\.(png|jpg|jpeg|gif|svg|webp|css|js|json|xml|woff2?|ttf|'
                       r'eot|mp4|webm|zip|rar|exe|dmg|psd|ai|eps|html?|php|asp)$', re.I)


# Trades that are definitely not ours, even if they mention 'sports'.
OTHER_TRADE = re.compile(
    r'(pipes and fittings|pipe fittings|plumbing|valves?|flanges?|'
    r'hardware|fasteners?|cement|construction material|tiles?|ceramic|'
    r'auto spare parts|automotive parts|car mats|cement|steel|aluminium|'
    r'printer|copier|toner|office supplies|medical|pharmaceutical|'
    r'food|beverage|spice|rice|tea|coffee|cashew|nuts|'
    r'prayer mat|carpet|rug|linoleum|vinyl flooring|rubber flooring)', re.I)


def title_hint(html):
    m = re.search(r'<title[^>]*>(.*?)</title>', html, re.S | re.I)
    return strip_tags(m.group(1)) if m else ''


# Domains a small company may legitimately publish its contact address on.
ALLOWED_MAIL_DOMAINS = re.compile(
    r'(omantel\.net\.om|batelco\.com\.bh|etisalat\.ae|e&\.com|'
    r'gmail\.com|hotmail\.com|outlook\.com|yahoo\.com|live\.com)', re.I)


def valid_email(e):
    """True only for an email that could actually receive mail."""
    if not e or not VALID_EMAIL.match(e):
        return False
    if JUNK_TLD.search(e):
        return False
    local = e.split('@')[0]
    # a filename-ish local part
    if local.count('.') >= 2 or local.startswith('-') or local.endswith('-'):
        return False
    if re.match(r'^[0-9a-f]{16,}$', local):        # a hash or a uuid
        return False
    dom = e.split('@')[1]
    if dom.count('.') < 1:
        return False
    return True

# Company names that are not useful as a search key.
JUNK_NAME = re.compile(
    r'^(new company|company|test|yard|auto parts|diamond auto spare parts|'
    r'amin|just4girls|sannad|afaq|afaq|new|company ltd|company llc)$', re.I)

UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/156.0.0.0 Safari/537.36')


def load_json(p, d):
    try:
        return json.load(open(p))
    except Exception:
        return d


def curl(url, timeout=22, retries=2):
    """Fetch a url. Some hosts fail intermittently, so retry a couple of
    times before giving up on a page that clearly exists."""
    for attempt in range(retries + 1):
        try:
            r = subprocess.run(
                ['curl', '-sL', '--max-time', str(timeout), '-A', UA,
                 '--retry', '1', '--retry-delay', '2',
                 '-H', 'Accept-Language: en-US,en;q=0.9', url],
                capture_output=True, text=True, timeout=timeout + 10)
            out = r.stdout or ''
            if out.strip():
                return out
        except Exception:
            pass
        if attempt < retries:
            time.sleep(1.5)
    return ''


def site_domain(url):
    m = re.match(r'https?://([^/]+)', url)
    if not m:
        return ''
    d = m.group(1).lower().split(':')[0]
    return d[4:] if d.startswith('www.') else d


def strip_tags(html):
    t = re.sub(r'(?is)<script.*?</script>', ' ', html)
    t = re.sub(r'(?is)<style.*?</style>', ' ', t)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = re.sub(r'&[a-z]+;', ' ', t)
    return re.sub(r'\s+', ' ', t)


# Words that appear in almost every trading company name. They must NOT be
# used to confirm a match - otherwise 'One Tailor Clothing and Apparel
# Stitching' matches any site with the word 'apparel' on it (it matched a US
# custom-clothing manufacturer, which is a COMPETITOR, not the Oman buyer).
GENERIC_WORDS = {
    'llc', 'ltd', 'limited', 'inc', 'co', 'company', 'corp', 'corporation',
    'group', 'of', 'and', 'cont', 'contracting', 'trading', 'the', 'international',
    'est', 'establishment', 'sa', 'wll', 'sarl', 'pte', 'plc', 'gmbh', 'bv',
    'holding', 'holdings', 'general', 'part', 'partners', 'global', 'services',
    'enterprises', 'enterprise', 'industries', 'industry', 'store', 'shop',
    'clothing', 'apparel', 'textile', 'textiles', 'garments', 'garment',
    'printing', 'print', 'stitching', 'design', 'dgn', 'factory', 'fashion',
    'one', 'two', 'three', 'new', 'royal', 'prime', 'elite', 'star', 'sun',
    'moon', 'sky', 'green', 'blue', 'red', 'white', 'gold', 'silver',
    'supplies', 'supply', 'solutions', 'management', 'consulting', 'agency',
    'business', 'commerce', 'commercial', 'projects', 'project', 'works',
}


def company_tokens(name, distinctive_only=False):
    """Distinctive tokens from a company name, ignoring legal suffixes."""
    toks = [t for t in re.findall(r"[A-Za-z0-9']+", name or '')
            if len(t) > 2 and t.lower() not in GENERIC_WORDS]
    if distinctive_only:
        # the FIRST distinctive token is usually the brand name
        return toks[:1]
    return toks


# A phone number must not run into the NEXT number on the page. The old
# pattern was greedy enough to match '+971-55-299-7170 2006 1000' as one
# blob ('29971702006'), which produced nonsense dialled numbers.
# Phone extraction works on SEPARATED runs: a run of digits/spaces/hyphens
# is split into groups, and each group of 2-4 digits is a candidate.
# The old single regex was greedy enough to swallow two adjacent numbers
# ('+971-55-299-7170 2006 1000' became one blob '717020061000').
# International prefix -> country, for the phone we publish.
COUNTRY_DIAL = {
    'oman': '+968', 'malaysia': '+60', 'egypt': '+20', 'portugal': '+351',
    'israel': '+972', 'united arab emirates': '+971', 'saudi arabia': '+966',
    'qatar': '+974', 'kuwait': '+965', 'united states': '+1',
    'united kingdom': '+44', 'germany': '+49', 'france': '+33', 'spain': '+34',
    'italy': '+39', 'netherlands': '+31', 'poland': '+48', 'turkey': '+90',
    'brazil': '+55', 'mexico': '+52', 'canada': '+1', 'australia': '+61',
    'indonesia': '+62', 'vietnam': '+84', 'thailand': '+66', 'philippines': '+63',
    'nigeria': '+234', 'kenya': '+254', 'ghana': '+233', 'south africa': '+27',
    'russia': '+7', 'ukraine': '+380', 'japan': '+81', 'south korea': '+82',
    'pakistan': '+92',
}

PHONE_RUN_RE = re.compile(r'[+(]?\d[\d\s()./-]{6,}\d[)\s.-]*')
PHONE_GROUP_RE = re.compile(r'\d{2,4}')

def head_or_text(html, text):
    """The title plus the top of the body - where a site says what it is."""
    return (title_hint(html) + ' ' + text[:1200]).lower()


def phones_from_links(html):
    """Extract phone numbers from structured links on the page.

    A site's own contact links carry the number in full international form:
        <a href="https://wa.me/60163648600">016-3648600</a>
        <a href="tel:+60-16-2215480">016-2215480</a>
        <a href="tel:03-62417296">03-62417296 (Office)</a>
    These are far more reliable than scraping the page text, which mixes in
    licence numbers, years and two adjacent numbers.
    Returns (numbers, whatsapp_numbers).
    """
    nums = []
    wa = []
    for m in re.finditer(r'href="(?:https?://wa\.me/|tel:)([+0-9\s()./-]{6,20})"',
                         html, re.I):
        raw = m.group(1).strip()
        digits = re.sub(r'\D', '', raw)
        if not 8 <= len(digits) <= 15:
            continue
        # a wa.me link is always a FULL international number (60163648600)
        # - prefix it with '+'. A tel: link may be local ('03-62417296') -
        # leave it without a country code, never invent one.
        if raw.startswith('+'):
            norm = '+' + digits
        elif 'wa.me' in m.group(0).lower():
            norm = '+' + digits
        else:
            norm = digits
        if norm not in nums:
            nums.append(norm)
    # wa.me links are, by definition, WhatsApp-reachable mobiles
    for m in re.finditer(r'href="https?://wa\.me/([0-9]{8,15})"', html, re.I):
        d = '+' + m.group(1)
        if d not in wa:
            wa.append(d)
    return nums, wa


def find_phones(text, country):
    """Pull plausible business phone numbers out of page text.

    NEVER invent a country code. The old logic blindly prefixed the buyer's
    directory country, turning a UAE mobile into '+966 12914637' and a
    Maryland number into '+966 4105550127' - both wrong, and both would have
    been dialled.

    The page text is scanned for runs of digits; each run is split into
    2-4 digit groups so two adjacent numbers are never merged into one blob.

    Rules:
      * a number that already carries '+' or '00' is used as-is
      * a NANP number becomes +1
      * a bare local number is only prefixed when the page names that
        country; otherwise it is returned UNPREFIXED and flagged as local
    """
    dial = COUNTRY_DIAL.get((country or '').lower())
    names_country = bool(country) and bool(re.search(re.escape(country), text, re.I))
    out = []
    for m in PHONE_RUN_RE.finditer(text):
        run = m.group(0)
        # the '+' / country code belongs to the FIRST group of the run
        prefix = ''
        body_run = run
        pm = re.match(r'\+\d{1,4}[-.\s]?', run)
        if pm:
            prefix = '+' + re.sub(r'\D', '', pm.group(0))
            body_run = run[pm.end():]
        groups = PHONE_GROUP_RE.findall(body_run)
        if not groups:
            continue
        # A run may hold several numbers. If the groups total more than 12
        # digits, they are more than one number - take the FIRST sensible
        # combination and stop.
        combos = []
        if len(groups) == 1:
            combos = [groups]
        elif len(groups) == 2:
            combos = [[groups[0], groups[1]]]
        elif len(groups) == 3:
            combos = [[groups[0], groups[1], groups[2]], [groups[0], groups[1]]]
        else:
            combos = [groups[:3], groups[:2]]
        for combo in combos:
            digits = ''.join(combo)
            if not 8 <= len(digits) <= 15:
                continue
            if prefix:
                raw = prefix + ' ' + digits
            elif re.match(r'^\(\d{3}\)\s*\d{3}', run):
                raw = '+1 ' + digits
            elif dial:
                dc = dial.lstrip('+')
                if digits.startswith(dc) and len(digits) > len(dc) + 6:
                    raw = dial + ' ' + digits[len(dc):]
                elif names_country:
                    raw = dial + ' ' + digits
                else:
                    raw = digits + ' (local - country unconfirmed)'
            else:
                raw = digits
            if raw not in out:
                out.append(raw)
            break
        if len(out) >= 3:
            break
    return out


def emails_from(site, country=''):
    """Pull emails from the site and its contact/about pages.

    Falls back to the REAL BROWSER when curl finds nothing - many small
    company sites are JavaScript-rendered, so curl gets the shell but not the
    content (Muscat Sports had no email in its curl output but its contact
    page does render in a browser).
    """
    found = {}
    home = curl(site, timeout=20)
    pages = [site]
    for m in re.finditer(r'href="([^"]*(?:contact|about|enquir|contact-us|get-in-touch)[^"]*)"',
                         home, re.I):
        u = m.group(1)
        if u.startswith('/'):
            u = urllib.parse.urljoin(site, u)
        if u.startswith('http') and u not in pages:
            pages.append(u)
    # Also try the obvious contact paths directly - many small sites use a
    # non-obvious name ('/contactus', '/contact-us.html', '/Contact.php') and
    # a link on the homepage may not be a plain href.
    base = site.rstrip('/')
    for cand in ('/contact', '/contactus', '/contact-us', '/contact.html',
                 '/contactus.php', '/Contact.php', '/about', '/about-us'):
        u = base + cand
        if u not in pages:
            pages.append(u)
    # PHP sites put the contact page under the app root:
    # '/index.php/contactus' is a very common shape.
    for cand in ('/index.php/contactus', '/index.php/contact-us',
                 '/index.php/contact', '/index.php/about', '/index.php/aboutus',
                 '/index.php/en/contact', '/index.php/en/contact-us'):
        u = base + cand
        if u not in pages:
            pages.append(u)
    for u in pages[:12]:
        html = home if u == site else curl(u, timeout=14)
        if not html:
            continue
        for m in re.finditer(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', html):
            e = m.group(0).lower()
            if 'example' in e or 'sentry' in e or 'wixpress' in e:
                continue
            if not BAD_LOCAL.match(e) and valid_email(e):
                found[e] = found.get(e, 0) + 1
    if not found:
        try:
            from site_emails import browser_emails
            for u in pages[:6]:
                em, body = browser_emails(u)
                for e in em:
                    if valid_email(e):
                        found[e] = found.get(e, 0) + 1
                if found:
                    break
        except Exception:
            pass
    return found


def search_company(name, country):
    """Search via the real browser - every curl search engine is blocked."""
    from browser_search import search as bsearch
    toks = company_tokens(name)
    kw = ' '.join(toks[:3]) if toks else name
    queries = [
        '"%s"' % name,
        '%s %s' % (kw, country),
        '%s contact email' % name,
    ]
    out = []
    for q in queries:
        try:
            out.extend(bsearch(q))
        except Exception:
            pass
        if len(out) >= 20:
            break
    return out


def process(comp):
    name = comp['company']
    country = (comp.get('dir_country') or '').replace('-', ' ').title()
    toks = company_tokens(name)
    if not toks:
        return None
    seen_domains = set()
    for href, title in search_company(name, country):
        d = site_domain(href)
        if not d or d in seen_domains:
            continue
        if any(x in d for x in ('bing.com', 'duckduckgo.com', 'linkedin.com',
                                'facebook.com', 'instagram.com', 'youtube.com',
                                'twitter.com', 'wikipedia.org', 'go4worldbusiness.com',
                                'amazon.', 'ebay.', 'alibaba.', 'pinterest.', 'reddit.')):
            continue
        if not re.search(r'\.(com|net|org|io|co|ae|sa|pk|in|my|eg|pt|tr|uk|us)$', d):
            continue
        if NOT_A_COMPANY.search(d):
            continue
        html = curl(href, timeout=20)
        if not html:
            # The site may be flaky. Do NOT mark the domain as seen - a later
            # url on the same domain (a contact page) may work. supasportsman
            # .com returned empty on its home page but worked on
            # /index.php/contactus.
            continue
        # only now mark the domain seen - we have a page from it
        seen_domains.add(d)
        if DEAD_SITE.search(html):
            continue
        if TEMPLATE_SITE.search(html):
            continue
        if GAMBLING_SITE.search(html):
            continue
        if CHALLENGE_WALL.search(html):
            continue
        text = strip_tags(html)
        low = text.lower()
        if INFO_SITE.search(head_or_text(html, text)):
            continue
        if not PRODUCT_WORDS.search(text):
            continue
        # The product must be the company's actual business, not a passing
        # mention in a footer. 'Blue Chip Global - Pipes and Fittings
        # Suppliers' passed on the word 'sports' somewhere in its page; the
        # title and the top of the body have to show our product.
        head = (title_hint(html) + ' ' + text[:900]).lower()
        if not PRODUCT_WORDS.search(head):
            continue
        # and it must not be obviously a different trade
        if OTHER_TRADE.search(text[:1200]):
            continue
        # ...nor a different sport
        if OTHER_SPORTS.search(head):
            continue
        if RETAIL_WORDS.search(text) and not WHOLESALE_WORDS.search(text):
            continue
        # The company name must actually be on the site, and the MATCH must
        # be on the distinctive token - in the domain or the page title, not
        # just buried in the body text.
        name_ok = False
        for t in toks:
            if t.lower() in low:
                name_ok = True
                break
        if not name_ok:
            continue
        distinct = company_tokens(name, distinctive_only=True)
        title = ''
        tm = re.search(r'<title[^>]*>(.*?)</title>', html, re.S | re.I)
        if tm:
            title = strip_tags(tm.group(1)).lower()
        dparts = d.replace('-', ' ').replace('.', ' ').lower()
        sig_ok = False
        for t in distinct:
            tl = t.lower()
            if tl in dparts or tl in title:
                sig_ok = True
                break
        if not sig_ok:
            # the domain may be a brand name we cannot split, but the TITLE
            # still has to carry the distinctive token together with the
            # country - e.g. 'SUPA SPORTSMAN OMAN | For Quality Sports Goods'
            if country and country.lower() in title and distinct:
                if any(t.lower() in title for t in distinct):
                    sig_ok = True
        if not sig_ok:
            continue
        emails = emails_from(href, country)
        # a phone number is just as usable as an email - it opens the WhatsApp
        # channel, and these buyers often publish a phone but no email.
        #
        # PREFER THE CONTACT PAGE: the homepage carries a footer switchboard
        # and the contact page carries the sales/mobile number. For Cobra
        # Sports the homepage gave +60 36217296 (a landline) while the
        # contact page also lists the mobile +60 16-2215480.
        # PREFER STRUCTURED LINKS over page text. A site's own wa.me / tel:
        # hrefs carry the full international number, so there is nothing to
        # guess and nothing to merge. Only fall back to text scraping.
        phones = []
        for cand in (href.rstrip('/') + '/contact-us',
                     href.rstrip('/') + '/contact',
                     href.rstrip('/') + '/contacts',
                     href):
            if site_domain(cand) != d:
                continue
            ch = curl(cand, timeout=16)
            if not ch:
                continue
            if site_domain(cand) != d:
                continue
            if CHALLENGE_WALL.search(ch) or TEMPLATE_SITE.search(ch):
                continue
            link_nums, wa_nums = phones_from_links(ch)
            if wa_nums:
                phones = wa_nums          # a WhatsApp mobile is the best target
                break
            if link_nums:
                phones = link_nums
                if cand.rstrip('/') != href.rstrip('/'):
                    break
                continue
            got = find_phones(strip_tags(ch), country)
            if got:
                phones = got
                if cand.rstrip('/') != href.rstrip('/'):
                    break          # the contact page wins
        if not emails and not phones:
            continue
        # The email MUST be on the company's own domain, OR on a domain the
        # company itself publishes the address on (a small Omani firm may
        # use its omantel.net.om address). A random address found in the
        # page text ('order@rand.org') is not this company.
        own = {}
        for e, score in emails.items():
            dom = e.split('@')[1]
            if dom == d or d.endswith(dom) or dom.endswith(d):
                own[e] = score + (20 if GOOD_ROLE.match(e) else 8)
            elif ALLOWED_MAIL_DOMAINS.search(dom):
                own[e] = score + 4
        best = None
        for e, score in own.items():
            if best is None or score > best[1]:
                best = (e, score)
        if not best and not phones:
            continue
        return {'email': best[0] if best else '',
                'phone': phones[0] if phones else '',
                'website': 'https://' + d,
                'matched': name, 'country': country,
                'category': comp.get('dir_category', '')}
    return None


LOCK = '/home/ubuntu/company_reach.lock'


def acquire_lock():
    """Exclusive lock on leads.csv - two reachers writing at once lost leads."""
    import errno
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
                print('another company_reach is running (pid %d) - exiting' % pid)
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
    limit = 25
    if '--limit' in args:
        limit = int(args[args.index('--limit') + 1])
    harvest = load_json(HARVEST, {})
    state = load_json(STATE, {'processed': {}})
    done = state.get('processed', {})
    todo = []
    for k, v in harvest.items():
        if k in done:
            continue
        if JUNK_NAME.match((v.get('company') or '').strip()):
            done[k] = {'status': 'junk-name'}
            continue
        todo.append((k, v))
    todo = todo[:limit]
    print('buyer companies harvested: %d | processed: %d | to try: %d'
          % (len(harvest), len(done), len(todo)))
    if not todo:
        print('nothing new')
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
    existing = {(r[idx['Email']] or '').strip().lower()
                for r in rows[1:] if len(r) > idx['Email']}
    existing_rows = rows[1:]   # for the one-contact-one-company guard
    new_rows = []          # rows to append safely at the end

    added = 0
    for i, (kid, comp) in enumerate(todo, 1):
        name = comp.get('company', '')
        print('[%d/%d] %s (%s) ...' % (i, len(todo), name[:44], comp.get('dir_country')))
        try:
            hit = process(comp)
        except Exception as e:
            print('    error: %s' % str(e)[:90])
            hit = None
        if hit:
            # FINAL SELF-CHECK: re-fetch the site and confirm the product and
            # the company are really there. A flaky site can pass once and
            # fail on the next fetch, and the site can have changed.
            chk = curl(hit['website'], timeout=18)
            if not chk:
                print('    final check failed (site unreachable) - skipping')
                done[kid] = {'status': 'no-match', 'note': 'final check failed'}
                continue
            ctext = strip_tags(chk)
            chead = (title_hint(chk) + ' ' + ctext[:900]).lower()
            if not PRODUCT_WORDS.search(chead) or OTHER_TRADE.search(ctext[:1200]) \
                    or OTHER_SPORTS.search(chead) or NOT_A_COMPANY.search(hit['website']):
                print('    final check failed (site no longer matches) - skipping')
                done[kid] = {'status': 'no-match', 'note': 'final check failed'}
                continue
            email = hit.get('email') or ''
            phone = hit.get('phone') or ''
            if email and email in existing:
                print('    dup: %s' % email)
                done[kid] = {'status': 'duplicate', 'email': email}
            else:
                maxid += 1
                row = [''] * len(hdr)
                row[idx['Lead ID']] = 'L%d' % maxid
                row[idx['Name']] = name[:70]
                row[idx['Type']] = 'Buyer company (go4WorldBusiness directory)'
                row[idx['Country']] = hit['country']
                row[idx['Email']] = email
                row[idx['Phone']] = phone
                row[idx['Website']] = hit['website']
                row[idx['Status']] = ('HUNTED (g4wb buyer company %s): %s - %s. '
                                      'Found in the go4WorldBusiness buyer directory and '
                                      'reached on its own site, so the platform 1/day '
                                      'inquiry limit does not apply.%s'
                                      % (time.strftime('%Y-%m-%d'), name[:50],
                                         comp.get('dir_category', ''),
                                         (' Contact phone %s (WhatsApp reachable).' % phone)
                                         if phone and not email else ''))
                row[idx['Profile Analysis']] = (
                    'Buyer company listed in the go4WorldBusiness buyer directory under %s. '
                    'Listed country: %s. Directory profile: %s. '
                    'Company website found independently: %s. Sales email: %s. '
                    'Trade: martial arts / sportswear manufacturing and export.'
                    % (comp.get('dir_category', ''), comp.get('dir_country', ''),
                       comp.get('href', ''), hit['website'], email))
                row[idx['Notes']] = 'go4WorldBusiness buyer company - ' + comp.get('href', '')

                # ONE contact may belong to ONE company only.
                #
                # A stale run added 'Shuaib' AND 'Ameer' with the SAME phone
                # (+968 20012026) and the SAME website (definitions.net) -
                # two different names on one contact is a false positive.
                # If this phone or this website is already held by a
                # DIFFERENT company name, reject this one.
                clash = False
                for r in existing_rows:
                    try:
                        rn = (r[idx['Name']] or '').strip().lower()
                        rp = (r[idx['Phone']] or '').strip()
                        rw = (r[idx['Website']] or '').strip().lower()
                    except Exception:
                        continue
                    if not rn or rn == name.strip().lower():
                        continue
                    if phone and rp and rp == phone.strip():
                        print('    REJECTED %s - phone %s already belongs to "%s"'
                              % (name[:30], phone[:20], rn[:28]))
                        clash = True
                        break
                    if hit['website'] and rw and rw == hit['website'].strip().lower():
                        print('    REJECTED %s - website %s already belongs to "%s"'
                              % (name[:30], hit['website'][:24], rn[:28]))
                        clash = True
                        break
                if clash:
                    done[kid] = {'status': 'contact-clash'}
                    continue

                new_rows.append(row)
                existing.add(email)
                added += 1
                print('    ADDED %s | %s | %s | %s' % (row[idx['Lead ID']], name[:30],
                                                       (email or ('phone:' + phone)),
                                                       hit['website']))
                done[kid] = {'status': 'added', 'email': email, 'phone': phone,
                             'lead': row[idx['Lead ID']]}
        else:
            print('    no match')
            done[kid] = {'status': 'no-match'}
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
    print('added %d contactable buyer companies | leads.csv now %d rows' % (added, len(_live_rows())))


if __name__ == '__main__':
    main()
