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
    r'sports kit|custom kit|team kit|football kit|jersey|'
    # General APPAREL / uniform makers. A school-uniform or workwear
    # manufacturer is a real buyer of ours - fashquedesigns.com ("Online
    # Clothing Wholesale Suppliers Vendors") was rejected because none of
    # these words were in the list.
    r'clothing (wholesale|supplier|manufacturer)|apparel (wholesale|supplier|manufacturer)|'
    r'garment (wholesale|supplier|manufacturer|factory)|'
    r'uniform (supplier|manufacturer|factory|maker)|'
    r'workwear|work wear|coverall|coveralls|'
    r'school uniform|corporate uniform|hospitality uniform|'
    r'military uniform|police uniform|institutional uniform|'
    r'activewear|athleisure|loungewear|'
    r'blank ?t-shirt|custom t-shirt|screen print|embroidery)', re.I)

# Sports that are NOT our line. A golf results site ('golfscale.com' -
# "Bridging the worlds of Professional Golf") matched on 'sports equipment'.
# A combat sport on the page. If one is present, the company sells or
# teaches martial arts, whatever else it also does.
COMBAT_SPORT_WORDS = re.compile(
    r'(martial art|karate|judo|taekwondo|kickboxing|kick ?boxing|'
    r'boxing|mma|mixed martial|bjj|jiu[- ]?jitsu|muay ?thai|'
    r'wushu|sanda|kung ?fu|aikido|hapkido|jeet ?kune ?do|'
    r'fencing|combat sport|self defence|self defense|'
    r'fight (?:wear|gear|short|shorts)|boxing glove|'
    r'dobok|gi |karate gi|judo gi)', re.I)

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
# An academy, sports centre, gym or club chain BUYS club gear for its
# own members. They are customers, not manufacturers.
ACADEMY_WORDS = re.compile(
    r'(sports academ|academ(?:y|ies)|sports cent(?:er|re)|sports club|'
    r'gym|fitness cent|training cent|martial arts (?:school|cent|academy)|'
    r'boxing (?:club|gym|academy)|taekwondo|judo|karate|'
    r'sports camp|sports school|dojo|fight (?:club|school|academy)|'
    r'venues? across|our venues)', re.I)

OTHER_TRADE = re.compile(
    r'(pipes and fittings|pipe fittings|plumbing|valves?|flanges?|'
    r'hardware|fasteners?|cement|construction material|tiles?|ceramic|'
    r'auto spare parts|automotive parts|car mats|cement|steel|aluminium|'
    r'printer|copier|toner|office supplies|medical|pharmaceutical|'
    r'food|beverage|spice|rice|tea|coffee|cashew|nuts|'
    # PACKAGING AND PRINTING. These surface under an apparel or
    # 'uniform' category but trade in wrappers, cartons and ink, not
    # garments. 'al tamayoz al raqi co.' says 'Packaging Materials' in
    # its title and sells 'the first wrap to the final seal'.
    r'packaging material|packaging suppl|packaging and print|'
    r'carton|corrugated|shrink wrap|stretch film|polypropylene|'
    r'printed packaging|labels and print|'
    # NOT 'screen print' - Apparel Point Trading is a real uniform
    # supplier that offers screen printing as a service. That is a
    # garment service, not a packaging trade.
    r'paper products|paper suppl|disposable cup|plastic cup|'
    r'food packaging|packaging solution|wrapping material|'
    r'prayer mat|carpet|rug|linoleum|vinyl flooring|rubber flooring|'
    # trades that surface under a 'sports' or 'apparel' category but
    # cannot buy our goods:
    r'lighters?|cigar|kerosene|usb lighter|'
    r'first communion|christening|communion dress|tuxedo|formal wear|'
    r'wedding dress|bridal|evening gown|'
    # a sports AGENCY or academy is not a manufacturer and does not buy
    # uniforms to resell:
    r'full service agency|brand agency|advertising agency|'
    r'event management|sports agency|athlete management|'
    r'photography|film production|video production|'
    # business DIRECTORIES and aggregators list companies but are not
    # them. easyoman.com is 'Find Businesses in Oman | 4,362+ Listings'.
    r'find businesses|\d[,\.]\d{3}\+?\s*listings|business directory|'
    r'listing[s]?|company profile|yellow pages|'
    # a UN / reference / academic site is not a buyer
    r'independent reference|not a un publication|'
    r'encyclopaedia|encyclopedia|academic reference)', re.I)


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
    # PLACEHOLDER addresses. 'john@doe.com' is the Lorem Ipsum of
    # emails - bidandwinauto.com published one and it was about to be
    # recorded as a buyer contact.
    #
    # The DOMAIN is what makes an address a placeholder. 'john@doe.com'
    # is a placeholder; 'john@johnaboxing.com' is a REAL boxing gym, and
    # that lead was nearly deleted over the local part alone.
    # The placeholder DOMAIN must be the WHOLE domain - 'my-club.it' is a
    # real gym in Padova, and 'my-club' contains 'my'. Only an exact
    # placeholder domain counts.
    _pl, _, _pd = e.partition('@')
    if _pd.lower() in ('doe.com', 'doe.org', 'doe.net', 'example.com',
                       'example.org', 'example.net', 'domain.com',
                       'email.com', 'name.com', 'test.com', 'company.com',
                       'yourdomain.com', 'mydomain.com', 'yourname.com',
                       'companyname.com', 'email.org', 'email.net'):
        return False
    if re.search(r'^(email|domain|name|test|company|your|my|example|site|'
                 r'web|mail|host)[0-9]*\.(com|org|net|co|io|info|biz)$',
                 _pd, re.I):
        return False
    # a generic local part is only a placeholder when the domain is
    # generic too - otherwise it is a real person.
    _local, _, _dom = e.partition('@')
    _generic_local = re.match(
        r'^(john|jane|james|mary|foo|bar|baz|abc|xyz|test|testing|asdf|'
        r'qwerty|sample|demo|your|you|user|example|name|email|info|'
        r'contact|admin|office)@', e, re.I)
    # the domain must be ENTIRELY generic: 'myclub.it' is a real gym,
    # 'my-club.it' is a real gym, only 'my.com' or 'my-domain.com' are
    # placeholders. A domain with any real word in it is a real domain.
    _generic_dom = re.fullmatch(
        r'(email|domain|name|test|company|your|my|example|site|web|mail|'
        r'host|info|sales|contact)[0-9]*'
        r'([.:\-](email|domain|name|test|company|your|my|example|site|'
        r'web|mail|host|info))?\.(com|org|net|co|io|info|biz|site|online)',
        _dom, re.I)
    if _generic_local and _generic_dom:
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

# ---------------------------------------------------------------- dead leads --
# The go4WorldBusiness buyer directory lists BUYER CONTACTS, so a large
# share of the "companies" are a PERSON'S name ("Chetan Kandhari",
# "Amer Nisar") or a firm in a completely different trade ("Power & Sun
# Solar Equipment", "Blue Waves Marine Equipments"). Those cannot be
# searched for as businesses - a person's name finds other people.
#
# 577 of the 990 queued companies were dead leads. Every one of them cost
# a web search plus a page fetch, so the nightly run spent hours proving
# nothing.
#
# A trading company IS a legitimate buyer, so "Fatima Trading" and "Zama
# Trading" stay. The test is: a person's name, an off-trade word, or a
# name in our product category that carries no trade word at all.
FIRST_NAMES = set(
    'ali ahmed mohammad mohammed abdullah abdul rashid khalid sultan hassan '
    'hussein ibrahim omar osama saeed yousef yusuf zayed saif hamed fahad '
    'nasser tariq firas shahab wafa ameer shuaib dima rima bravo private '
    'fayyaz akash fatima maryam aisha khadija zainab layla noor rehan waqar '
    'kamran adnan bilal tanveer asim fawad irfan junaid kashif moez nadeem '
    'qais raheel sami taimoor waleed xavier zubair chetan chettan amer '
    'nishikant shahid raja khan kandhari shetty shirke nisar ansari singh '
    'patel kumar reddy rao naidu menon iyer bhatt jain gupta sharma verma '
    'kaur malhotra chopra bhalla dhillon grewal sidhu bhagat desai makar '
    'sethi bhatia ahluwalia gill sandhu khaled mansour saleh hamad dawood '
    'iqbal jaffery farooq latif rizvi qureshi sheikh butt bhatti abbasi '
    'ashraf baig chowdhury das ghosh jadhav kamble mahajan more patil '
    'thakur tiwari varma yadav zaware radhika gayathri devi lakshmi priya '
    'pooja rekha sunita vladimir sergei alexei dmitri oleg yuri andrey '
    'pavel mikhail nikolai abraham'.split())

# A firm in a trade that cannot buy martial-arts apparel.
OFF_TRADE = re.compile(
    r'(solar|petroleum|marine|packaging|airways|air |hotel|restaurant|medical|'
    r'food|electrical|chemical|automotive|construction|real estate|consult|'
    r'freight|logistic|cargo|oil|gas|bank|insur|account|audit|tax|legal|'
    r'hospitality|travel|tour|agency|advertis|marketing|media|software|'
    r'technology|solutions|systems|consultancy|holding|investment|finance)', re.I)

# A name that IS about our product space.
OUR_TRADE = re.compile(
    r'\b(sport|sporting|athletic|gym|fitness|martial|karate|taekwondo|judo|'
    r'boxing|fighter|combat|fight|uniform|apparel|clothing|wear|kit|gloves?|'
    r'glove|equip(ment)?|suppl(y|ies)|train(ing|er)?|dojo|academy|club|team|'
    r'champion|arena|boxe|active|fit|pro\b|legacy|'
    r'kick ?pad|kickbox|muay|tae ?kwon|jiu ?jitsu|bjj|'
    r'head ?gear|shin ?guard|hand ?wrap|mouth ?guard|'
    r'fight ?wear|fight ?short|sparring|bum ?guard|'
    r'uniform|gi\b|dobok|karate ?gi|'
    r'factory|manufacturer|supplier|wholesale|distributor|'
    r'boxing|boxer|protector)', re.I)

# A name that could still be a business.
COULD_BE_BUSINESS = re.compile(
    r'\b(trading|co\b|llc|ltd|group|international|store|shop|company|est\b|'
    r'general|enterprise|world|star|zone|genius|nsrit|altx|ats\b|bt\b)', re.I)

OUR_CATEGORIES = {
    'karate-uniforms', 'team-uniforms', 'martial-arts-gloves', 'boxing-gloves',
    'uniforms', 'protective-equipment', 'fight-wear', 'kick-pads', 'hand-wraps',
    'mouth-guards', 'sports-apparel', 'sports-goods-equipments', 'sportswear',
    'sports-accessories', 'martial-arts-mats', 'martial-arts-belts',
    'sports-jerseys',
}


# ------------------------------------------------------- the real filter ----
# The directory CATEGORY is unreliable. A company listed under
# 'martial-arts-gloves' may actually 'Buys industrial gloves, latex gloves',
# and one listed under 'sportswear' may 'Buys inflatable rugby ball'.
#
# The go4WorldBusiness member profile states what the buyer actually buys
# in one sentence:
#     'Koreca Glove Industry is a junior buyer from Daegu, South Korea.
#      Buys industrial gloves, latex gloves.'
#
# That sentence is the ONLY reliable signal. Reading it costs one profile
# fetch per company, but it replaces a web search plus a page fetch, and
# it stops the funnel chasing buyers who want inflatable rugby balls.
BUYS_RE = re.compile(r'\.\s*(Buys|Buying)\s+([^\n]{0,170})', re.I)

# What we actually manufacture.
OUR_PRODUCTS = re.compile(
    r'(martial art|judo|karate|taekwondo|bjj|brave ?jitsu|boxing|'
    r'kickbox(?:ing)?|mma|mixed martial|fight ?wear|combat sport|'
    r'self[- ]defen[cs]e|uniform|dobok|karate gi|'
    r'sport uniform|team wear|boxing glove|sparring|headgear|'
    r'shin guard|mouth guard|hand wrap|'
    # 'belt' only counts in a martial-arts sense - 'seat belt' and 'wire
    # hanger' are not belts we make.
    r'karate belt|black belt|rank belt|belt\b(?!\s*(?:belt|webbing))|'
    r'(?<!seat )(?<!car )belt)', re.I)

# Products that look adjacent but are a different industry entirely.
NOT_OUR_PRODUCTS = re.compile(
    r'(industrial glove|latex glove|nitrile|medical glove|work glove|'
    r'safety glove|cleaning glove|chemical glove|food grade glove|'
    r'household glove|golf item|cricket ball|rugby ball|football|'
    r'basketball|soccer ball|volleyball|tennis|badminton|swim|'
    r'housekeeping|hand towel|towel|food and beverage|'
    r'menswear|womenswear|kidswear|knits|woven|'
    r'inflatab|beach|swimwear|fashion accessory|jewell|eyewear|'
    r'shoe|footwear|bag\b|umbrella|watch|cap\b|hat\b|'
    # not ours, even though the word 'uniform' can appear nearby
    r'disposable medical|surgical|laundry hanger|wire hanger|'
    r'lab coat|disposable apron|'
    # 'belt' in a car/seat context
    r'seat belt|steering wheel|car belt)', re.I)


def buyer_wants(html):
    """Return the phrase the buyer says they buy, or None."""
    if not html:
        return None
    t = strip_tags(html)
    m = BUYS_RE.search(t)
    if not m:
        return None
    return (m.group(1) + ' ' + m.group(2)).strip()


def profile_verdict(buys):
    """'ours' | 'theirs' | 'unknown' for the phrase the buyer states."""
    if not buys:
        return 'unknown'
    if NOT_OUR_PRODUCTS.search(buys):
        return 'theirs'
    if OUR_PRODUCTS.search(buys):
        return 'ours'
    return 'unknown'


def is_dead_lead(name, category):
    """True when the entry cannot be searched for as a business."""
    n = (name or '').strip()
    if not n:
        return True
    words = [w for w in re.split(r'[\s,&.]+', n) if w]
    if len(words) == 1 and words[0].lower() in FIRST_NAMES:
        return True
    if len(words) == 2 and all(w.lower() in FIRST_NAMES for w in words):
        return True
    if OFF_TRADE.search(n):
        return True
    if category in OUR_CATEGORIES:
        if not OUR_TRADE.search(n) and not COULD_BE_BUSINESS.search(n):
            return True
    return False

UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/156.0.0.0 Safari/537.36')


def load_json(p, d):
    try:
        return json.load(open(p))
    except Exception:
        return d


# A go4WorldBusiness rate-limit page is a short HTML stub (~2 KB) with no
# directory content. It is NOT an empty response, so the old 'if out.strip()'
# check accepted it and the crawler moved on with no data - and the harvest
# silently returned 0.
BLOCK_PAGE_MIN = 8000


def curl(url, timeout=22, retries=3):
    """Fetch a url. Some hosts fail intermittently, so retry a couple of
    times before giving up on a page that clearly exists.

    A SHORT response on a go4WorldBusiness page is a rate-limit stub, not
    the page. Treat it as a failure and retry with a backoff.
    """
    is_g4wb = 'go4worldbusiness.com' in url
    for attempt in range(retries + 1):
        try:
            r = subprocess.run(
                ['curl', '-sL', '--max-time', str(timeout), '-A', UA,
                 '--retry', '1', '--retry-delay', '2',
                 '-H', 'Accept-Language: en-US,en;q=0.9', url],
                capture_output=True, text=True, timeout=timeout + 10)
            out = r.stdout or ''
            if out.strip():
                if is_g4wb and len(out) < BLOCK_PAGE_MIN:
                    # a rate-limit stub - back off and try again
                    if attempt < retries:
                        time.sleep(4 + attempt * 4)
                        continue
                    return ''
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


def _is_vowelish(ch):
    """True for the letters that stand in for Arabic short vowels.

    'y' counts because it is used as a vowel in transliteration
    ('Tamayoz' for 'Tamauez').
    """
    return ch in 'aeiouy'


def _close_enough(a, b):
    """True when two tokens are near-identical (one letter apart).

    The directory said 'Fashqua Buying Company'; the company writes 'Fashque
    Designs'. A single-letter spelling difference must not kill the lead.

    It must also survive a TRANSPOSED pair of letters. The directory says
    'Al Tamauez Al Raqi LLC'; the company's own site says 'al tamayoz al
    raqi co.'. 'Tamauez' vs 'Tamayoz' is 'ue' swapped for 'uy' - one
    edit by Damerau-Levenshtein, but two by plain Levenshtein, so the
    old check rejected the company's own website.
    """
    a = (a or '').lower()
    b = (b or '').lower()
    if not a or not b:
        return False
    if a == b:
        return True
    # A TRANSPOSITION of two adjacent letters. Check it first: a
    # transposition keeps the length, so the edit-distance path below
    # would see two differences and reject it.
    if len(a) == len(b):
        diffs = [i for i in range(len(a)) if a[i] != b[i]]
        if len(diffs) == 2:
            i, j = diffs
            if j == i + 1 and a[i] == b[j] and a[j] == b[i]:
                return True
    # An ARABIC TRANSLITERATION VARIANT. The directory says 'Al Tamauez Al
    # Raqi LLC'; the company's own site says 'al tamayoz al raqi co.'.
    # 'Tamauez' and 'Tamayoz' differ at two positions and BOTH pairs are
    # vowels - 'ue' rendered as 'uy/o'. That is the same name, spelled
    # the way a different clerk spelled it.
    #
    # The rule is deliberately narrow, because a loose vowel rule starts
    # accepting different companies:
    #   - same length, at least 6 characters
    #   - exactly TWO positions differ
    #   - both sides of each difference are vowels
    #   - the CONSONANTS must be identical and in the same order
    #
    # 'Tamauez'/'Tamayoz' passes: consonants t-m-z at the same places.
    # 'Sultan'/'Soltan' fails: 'u' vs 'o' is a vowel change but the
    # consonant skeleton also shifts, and one vowel swap in a short word
    # is too weak a signal on its own.
    if len(a) == len(b) and len(a) >= 6:
        diffs = [i for i in range(len(a)) if a[i] != b[i]]
        if len(diffs) == 2 and all(_is_vowelish(a[i]) and _is_vowelish(b[i])
                                   for i in diffs):
            ca = ''.join(a[i] for i in range(len(a)) if i not in diffs)
            cb = ''.join(b[i] for i in range(len(b)) if i not in diffs)
            if ca == cb:
                return True
    if abs(len(a) - len(b)) > 1:
        return False
    # one insertion / deletion / substitution
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    i = j = 0
    diff = 0
    while i < len(shorter) and j < len(longer):
        if shorter[i] == longer[j]:
            i += 1
            j += 1
            continue
        diff += 1
        if diff > 1:
            return False
        j += 1
    return True


def fuzzy_name_match(tokens, distinctive, body_low, domain, title_low):
    """A spelling variant of the company name is still the company.

    A SHORT TOKEN MUST MATCH EXACTLY. 'Um Abdullah Global Projects'
    matched worldbody.org because 'Um' is one letter away from 'um' in
    'worldbody'. A 2-3 character token carries no information, so it can
    only ever match literally.
    """
    hay = (body_low or '') + ' ' + (domain or '') + ' ' + (title_low or '')
    words = re.findall(r'[a-z]{4,}', hay)
    for t in (distinctive or tokens):
        tl = t.lower()
        if tl in hay:
            return True
        if len(tl) <= 3:
            # too short to fuzzy-match against anything
            continue
        for w in words:
            if _close_enough(tl, w):
                return True
    return False


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
    for m in re.finditer(r'href="((?:https?://wa\.me/|tel:)[^"]{6,40})"',
                         html, re.I):
        _full = m.group(1).strip()
        # A MASKED number - 'tel:+971****8453' - is not dialable. The mask
        # is the site's own privacy filter. Check the FULL href: the
        # capture group stops at the '*', so the mask has to be looked for
        # before the number is extracted.
        if '*' in _full:
            continue
        raw = re.sub(r'^(?:https?://wa\.me/|tel:)', '', _full, flags=re.I)
        raw = raw.strip()
        if not re.fullmatch(r'[+0-9\s()./-]{6,25}', raw):
            continue
        # a wa.me number is always a bare digit string
        if 'wa.me' in _full.lower() and not raw.isdigit():
            continue
        digits = re.sub(r'\D', '', raw)
        if not 8 <= len(digits) <= 15:
            continue
        # a PLACEHOLDER phone - '+971 00 000 0000' is a CSS/JS mask that
        # some sites ship in their contact widget. It was being recorded
        # as a dialable contact.
        if set(digits) <= {'0'}:
            continue
        _local = digits
        for _cc in re.findall(r'\d{1,4}', raw[:6] if raw.startswith('+') else ''):
            pass
        if raw.startswith('+'):
            _cc = re.sub(r'\D', '', raw)[:3]
            if _cc and digits.startswith(_cc):
                _local = digits[len(_cc):]
        if not _local or set(_local) <= {'0'}:
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
        # a masked or placeholder wa.me link is not reachable
        if set(d) <= {'0', '+'}:
            continue
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
        # A REGISTRATION or VAT number is not a phone. cobra sports lists
        # 'COBRA SPORTS SDN BHD (NO. 207737-K NO. 199001016068)' - the
        # extractor turned the registration number into +60 199001016068.
        # A run that sits inside brackets right after 'NO.', 'REG', 'VAT',
        # 'CRN', 'LC' or 'GST' is an identifier, not a number to dial.
        _before = text[max(0, m.start() - 40):m.start()].lower()
        if re.search(r'\b(no|reg(?:istration)?|vat|crn|licen[cs]e|lc|gst|'
                     r'company no|reg\.?\s*no|ssm)\b[\s.:#-]{0,12}$',
                     _before):
            continue
        # A PLACEHOLDER phone: '+971 00 000 0000' is a CSS/JS mask, not a
        # number. desertlinktrading.com carried one and it was recorded as
        # a dialable contact. A real number has at least 7 significant
        # digits and is not all zeros.
        _digits = re.sub(r'\D', '', run)
        if len(_digits) < 7 or set(_digits) <= {'0'}:
            continue
        # strip the country code before the zero check - '+971 00 000 0000'
        # has digits '971000000000', which is not all zeros, but the number
        # AFTER the code is.
        # Strip whatever country code is present so the PLACEHOLDER check
        # sees the subscriber part. The code may differ from the
        # directory's country - desertlinktrading.com is listed under
        # saudi-arabia but its own mask says '+971 00 000 0000'.
        _local = _digits
        if _digits.startswith('00'):
            _local = _digits[2:]
        else:
            for _cc in (re.sub(r'\D', '', dial or ''),):
                if _cc and _digits.startswith(_cc):
                    _local = _digits[len(_cc):]
                    break
            else:
                # a leading '+<2-4 digits>' that is not the directory's
                # country - strip it anyway
                if len(_digits) > 7:
                    _local = _digits[3:] if len(_digits) - 3 >= 7 else _digits[4:]
        if not _local or set(_local) <= {'0'}:
            continue
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


# Countries a company names on its OWN site. The directory's country can
# be wrong - it lists the member's declared country, not where the
# website's contact details point.
SITE_COUNTRY_NAMES = {
    'United Arab Emirates': ['Dubai', 'UAE', 'Emirates', 'Abu Dhabi',
                             'Sharjah', 'Ajman', 'Ras Al Khaimah'],
    'Saudi Arabia': ['Saudi', 'Riyadh', 'Jeddah', 'Dammam'],
    'Oman': ['Oman', 'Muscat', 'Sohar'],
    'Kuwait': ['Kuwait'],
    'Qatar': ['Qatar', 'Doha'],
    'Egypt': ['Egypt', 'Cairo', 'Alexandria'],
    'Pakistan': ['Pakistan', 'Lahore', 'Karachi', 'Sialkot'],
    'Malaysia': ['Malaysia', 'Kuala Lumpur', 'Penang', 'Johor'],
    'Portugal': ['Portugal', 'Lisbon', 'Porto'],
    'Israel': ['Israel', 'Tel Aviv'],
    'India': ['India', 'Mumbai', 'Delhi', 'Ahmedabad', 'Surat', 'Coimbatore'],
    'Bangladesh': ['Bangladesh', 'Dhaka'],
    'Indonesia': ['Indonesia', 'Jakarta', 'Bali'],
    'Vietnam': ['Vietnam', 'Ho Chi Minh', 'Hanoi'],
    'Thailand': ['Thailand', 'Bangkok'],
    'Brazil': ['Brazil', 'Sao Paulo'],
    'Mexico': ['Mexico'],
    'Canada': ['Canada', 'Toronto', 'Vancouver'],
    'Australia': ['Australia', 'Sydney', 'Melbourne'],
    'Ukraine': ['Ukraine', 'Kyiv', 'Odessa'],
    'Japan': ['Japan', 'Tokyo', 'Osaka'],
    'South Korea': ['South Korea', 'Seoul', 'Busan'],
    'Turkey': ['Turkey', 'Istanbul', 'Izmir'],
}

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
        # B2B DIRECTORIES list the company but do not sell to us - the
        # contact on them is a listing agent, not the buyer. We need the
        # company's OWN site to find its real sales email.
        if any(x in d for x in ('company-listing.org', 'listcompany.org',
                                'exporthub.com', 'tradekorea.com', 'ec21.com',
                                'exportersindia.com', 'tradeindia.com', 'alibaba.',
                                'made-in-china.com', 'globalsources.com',
                                'importgenius.com', 'panjiva.com', 'kompass.com',
                                'europages.co.uk', 'yellow-pages.', 'yelp.com',
                                'yellowpages.', 'b2b.', 'tradeatlas.com',
                                'searchnature', 'firmedia', 'pitchbook.com',
                                'crunchbase.com', 'bloomberg.com', 'zoominfo.',
                                'listcompany', 'companylist', 'b2b-jp.com')):
            continue
        if not re.search(r'\.(com|net|org|io|co|ae|sa|pk|in|my|eg|pt|tr|uk|us)$', d):
            continue
        if NOT_A_COMPANY.search(d):
            continue
        seen_domains.add(d)
        html = curl(href, timeout=20)
        if not html:
            # The site may be flaky. Do NOT mark the domain as seen - a later
            # url on the same domain (a contact page) may work. supasportsman
            # .com returned empty on its home page but worked on
            # /index.php/contactus.
            continue
        # Only mark the domain seen once we have a page FROM it AND it has
        # passed the product tests. Marking it before the tests meant a
        # site rejected on one page could never be tried on another URL
        # of the same domain - and it was then skipped for the rest of
        # the company too.
        # (The domain IS still marked if the page could not be fetched -
        # a dead domain should not be retried endlessly.)
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
        # THE PRODUCT MUST BE VISIBLE ON THE SITE, OR THE DIRECTORY MUST
        # SAY SO AND THE SITE MUST BE A WHOLESALE BUSINESS.
        #
        # A general trading company whose site never says 'uniform' or
        # 'boxing' used to be rejected outright. But go4WorldBusiness
        # classified it as a buyer of martial-arts goods, and its own site
        # is a wholesale operation with a working sales email
        # (info@alwahaksa.com, info@desertlinktrading.com). The platform
        # knows what they buy; the site just does not advertise it.
        dir_cat = (comp.get('dir_category') or '').lower()
        dir_is_ours = bool(re.search(
            r'(uniform|karate|judo|taekwondo|boxing|fight|mma|martial|'
            r'belt|glove|head-?gear|head-?guard|shin-?guard|mouth-?guard|'
            r'hand-?wrap|kick-?pad|sportswear|sports-?wear|team-?wear|'
            r'protective|sport)', dir_cat))
        # A MINIMAL site lists no products at all (alwahaksa.com is one).
        # The platform's own classification plus a working email on the
        # company's own domain is enough for those.
        #
        # But a minimal site with NO product words and NO wholesale words
        # is not evidence of anything. litoonline.com is a children's
        # formal-wear shop (first communion dresses, tuxedos) that the
        # directory had filed under 'sportswear'. It must NOT be accepted
        # just because the page is small.
        _minimal = len(text) < 4500
        _name_on_page = any(t.lower() in low for t in toks)
        _is_academy = bool(ACADEMY_WORDS.search(text[:1500]))
        if not PRODUCT_WORDS.search(text):
            if not (dir_is_ours and
                    (WHOLESALE_WORDS.search(text) or _is_academy or
                     (_minimal and _name_on_page and len(text) > 900))):
                continue
        # The product must be the company's actual business, not a passing
        # mention in a footer. 'Blue Chip Global - Pipes and Fittings
        # Suppliers' passed on the word 'sports' somewhere in its page; the
        # title and the top of the body have to show our product.
        # The head window must be wide enough to reach the product
        # words. infinitesportsuae.com puts 'karate coaching' well below
        # the first 900 characters, so a narrow window rejected the
        # correct company and the domain was then marked seen - it never
        # got a second look.
        head = (title_hint(html) + ' ' + text[:3000]).lower()
        # An ACADEMY, SPORTS CENTRE or club chain is a legitimate buyer of
        # club gear - they issue gis and uniforms to their own students.
        # They are not manufacturers, so their site carries no product
        # words, but they do buy in volume.
        _is_academy = bool(ACADEMY_WORDS.search(head))
        if not PRODUCT_WORDS.search(text):
            if not (dir_is_ours and
                    (WHOLESALE_WORDS.search(head) or _is_academy or
                     (_minimal and _name_on_page and len(text) > 900))):
                continue
        # and it must not be obviously a different trade
        if OTHER_TRADE.search(text[:1200]):
            continue
        # ...nor a different sport
        # A MULTI-SPORT ACADEMY that also teaches a combat sport is a
        # buyer of ours. infinitesportsuae.com lists cricket, swimming,
        # gymnastics and basketball AND karate coaching - the combat sport
        # is what matters. Only reject another sport when NO combat sport
        # appears anywhere on the page.
        if OTHER_SPORTS.search(head) and not COMBAT_SPORT_WORDS.search(text):
            continue
        if RETAIL_WORDS.search(text) and not WHOLESALE_WORDS.search(text):
            continue
        # The company name must actually be on the site, and the MATCH must
        # be on the distinctive token - in the domain or the page title, not
        # just buried in the body text.
        distinct = company_tokens(name, distinctive_only=True)
        title = ''
        tm = re.search(r'<title[^>]*>(.*?)</title>', html, re.S | re.I)
        if tm:
            title = strip_tags(tm.group(1)).lower()
        dparts = d.replace('-', ' ').replace('.', ' ').lower()
        name_ok = False
        for t in toks:
            if t.lower() in low:
                name_ok = True
                break
        if not name_ok:
            # a spelling variant is still the same company
            name_ok = fuzzy_name_match(toks, distinct, low, d, title)
        if not name_ok:
            continue
        sig_ok = False
        for t in distinct:
            tl = t.lower()
            if tl in dparts or tl in title:
                sig_ok = True
                break
        if not sig_ok:
            # 'Fashqua' (directory) vs 'Fashque' (their site) - one letter
            # apart must still count as the distinctive token
            if fuzzy_name_match(distinct, distinct, dparts + ' ' + title, d, title):
                sig_ok = True
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
        # The site's own text may name a country that differs from the
        # directory's. desertlinktrading.com is listed under saudi-arabia
        # but its own site says 'Dubai' and 'FZCO'. The site is right.
        site_country = country
        for _cc, _names in SITE_COUNTRY_NAMES.items():
            if any(re.search(r'\b' + re.escape(n) + r'\b', text, re.I)
                   for n in _names):
                site_country = _cc
                break
        return {'email': best[0] if best else '',
                'phone': phones[0] if phones else '',
                'website': 'https://' + d,
                'matched': name, 'country': site_country,
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
                # The PID is alive - but it may be a DIFFERENT program that
                # inherited the PID after the real reacher died. Confirm it
                # is actually a company_reach before refusing to start.
                try:
                    _cmd = open('/proc/%d/cmdline' % pid, 'rb').read().decode(
                        'utf-8', 'replace').replace('\x00', ' ')
                except Exception:
                    _cmd = ''
                if 'company_reach' in _cmd:
                    print('another company_reach is running (pid %d) - exiting' % pid)
                    return False
                print('stale reach lock (pid %d is not a company_reach) - reclaiming' % pid)
                os.unlink(LOCK)
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


def _retry_count(prev):
    """How many times this company has already been retried."""
    if isinstance(prev, dict):
        return int(prev.get('tries') or 0)
    return 0


def _is_confirmed_buyer(kid):
    """True when the screen confirmed this company buys OUR product.

    A company that says on its own go4WorldBusiness profile that it buys
    uniforms / martial-arts gear is worth retrying when the web search
    fails to locate its site. Only companies with no such statement may
    be retired after one failed search.
    """
    try:
        with open('/home/ubuntu/g4wb_company_screened.json', encoding='utf-8') as f:
            sc = json.load(f)
        return kid in sc.get('ours', {})
    except Exception:
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
            # A buyer whose search failed is RETRYABLE, not done. The
            # plain `if k in done: continue` retired it forever, which is
            # how 20 verified buyers were lost. Let it back in until the
            # retry cap is reached.
            _st = done.get(k)
            _stt = _st.get('status') if isinstance(_st, dict) else _st
            if _stt == 'retry-buyer':
                if _retry_count(_st) >= 3:
                    continue          # cap reached - set aside for review
                # else: fall through and retry it
            else:
                continue
        if JUNK_NAME.match((v.get('company') or '').strip()):
            done[k] = {'status': 'junk-name'}
            continue
        if is_dead_lead(v.get('company'), v.get('dir_category')):
            # a person's name, or a firm in another trade - it cannot be
            # searched for as a business, so do not waste a search on it
            done[k] = {'status': 'dead-lead'}
            continue
        if (v.get('dir_country') or '').lower() == 'pakistan':
            # A PAKISTANI company on the buyer directory is a local
            # competitor or a local trader, not an export buyer. 36 of the
            # 43 companies that screened as 'ours' were Pakistani. They
            # are a different business entirely - chasing them wastes the
            # search budget on companies that cannot buy from us.
            done[k] = {'status': 'local-pakistan'}
            continue
        # THE DECISIVE CHECK: read the buyer's own go4WorldBusiness profile
        # and see what they say they buy. If it is not our product, stop
        # here - a web search for a buyer who wants inflatable rugby balls
        # can never succeed.
        prof = curl(v.get('href') or '', timeout=22)
        buys = buyer_wants(prof)
        verdict = profile_verdict(buys)
        if verdict == 'theirs':
            print('    skip - they buy: %s' % (buys or '')[:90])
            done[k] = {'status': 'wrong-product', 'buys': (buys or '')[:120]}
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
                # The site did not LOAD. For a confirmed buyer that is a
                # transient failure, not a rejection - the company still
                # states on its profile that it buys our product. Keep it
                # retryable instead of retiring it.
                if _is_confirmed_buyer(kid):
                    print('    confirmed buyer - site unreachable, re-queued')
                    done[kid] = {'status': 'retry-buyer', 'note': 'site unreachable'}
                else:
                    print('    final check failed (site unreachable) - skipping')
                    done[kid] = {'status': 'no-match', 'note': 'final check failed'}
                continue
            ctext = strip_tags(chk)
            chead = (title_hint(chk) + ' ' + ctext[:900]).lower()
            # The self-check must apply the SAME product rule as
            # process(), or it rejects exactly the companies process()
            # just accepted.
            _dcat = (comp.get('dir_category') or '').lower()
            _dours = bool(re.search(
                r'(uniform|karate|judo|taekwondo|boxing|fight|mma|martial|'
                r'belt|glove|head-?gear|head-?guard|shin-?guard|mouth-?guard|'
                r'hand-?wrap|kick-?pad|sportswear|sports-?wear|team-?wear|'
                r'protective|sport)', _dcat))
            _cminimal = len(ctext) < 4500
            _cname = any(t.lower() in ctext.lower()
                         for t in company_tokens(name))
            _cok = PRODUCT_WORDS.search(chead) or (
                _dours and (WHOLESALE_WORDS.search(chead) or
                            (_cminimal and _cname and len(ctext) > 900)))
            if not _cok or OTHER_TRADE.search(ctext[:1200]) \
                    or OTHER_SPORTS.search(chead) or NOT_A_COMPANY.search(hit['website']):
                # The site was FOUND but it does not match. For a company
                # the screen CONFIRMED, that is one bad candidate - the
                # company may have another site, or the next search may
                # surface it. Re-queue instead of retiring it.
                if _is_confirmed_buyer(kid):
                    tries = _retry_count(done.get(kid))
                    if tries >= 3:
                        done[kid] = {'status': 'buyer-no-site',
                                     'note': 'site did not match, 3 tries', 'tries': tries}
                        print('    confirmed buyer - 3 tries exhausted, set aside')
                    else:
                        done[kid] = {'status': 'retry-buyer',
                                     'note': 'site did not match', 'tries': tries}
                        print('    confirmed buyer - site did not match, re-queued (try %d)'
                              % (tries + 1))
                else:
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
                    if not rn:
                        continue
                    if rn == name.strip().lower():
                        # The SAME company is already in the tracker under
                        # another name spelling, or under the same name.
                        # A stale run added 'Muscat Sports Llc' as L5286
                        # when L5285 already held 'Muscat Sports LLC'.
                        print('    REJECTED %s - the same company is already '
                              'in the tracker' % name[:30])
                        clash = True
                        break
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
                # WRITE THE ROW NOW, not at the end of the batch. The
                # state file said 'added' while the row still sat in
                # memory - a kill between the two lost that lead FOREVER,
                # because the state marked it done so it was never retried.
                #
                # WRITE FIRST, THEN VERIFY. The verification used to run
                # BEFORE the write, so it checked a row that did not exist
                # yet and every single addition was rejected as
                # 'add-failed' - which is why the buyer-company count
                # never moved.
                from leads_safe_write import add_rows
                add_rows([row])
                new_rows = []
                # VERIFY the lead actually landed before recording
                # 'added'. A state file that claims 'added' for a lead
                # that is not in the tracker means the company is never
                # retried - the record is silently lost. Four entries
                # were in that state on 2026-11-08.
                _landed = False
                try:
                    import csv as _csv2
                    with open(CSV_PATH, newline='', encoding='utf-8-sig') as _f2:
                        _all = list(_csv2.reader(_f2))
                    _landed = any(_r and _r[0] == row[idx['Lead ID']]
                                  for _r in _all[1:])
                except Exception:
                    _landed = True      # cannot verify - do not block
                if not _landed:
                    print('    NOT LANDED - %s is not in leads.csv, '
                          're-queueing the company' % row[idx['Lead ID']])
                    done[kid] = {'status': 'add-failed',
                                 'email': email, 'phone': phone}
                    continue
                done[kid] = {'status': 'added', 'email': email, 'phone': phone,
                             'lead': row[idx['Lead ID']]}
        else:
            print('    no match')
            # A CONFIRMED BUYER whose web search failed is NOT done. The
            # company states on its own profile that it buys our product,
            # so it is worth trying again - the search simply did not find
            # its site this time.
            #
            # Marking it 'no-match' retired it forever, and 20 verified
            # buyers (police uniforms, military uniforms, school uniforms)
            # were retired that way. They are now re-queued.
            if _is_confirmed_buyer(kid):
                # Cap the retries. A confirmed buyer deserves more than one
                # attempt, but the search cannot find every site - after
                # three tries it is left for a manual look rather than
                # looping forever.
                tries = _retry_count(done.get(kid))
                if tries >= 3:
                    done[kid] = {'status': 'buyer-no-site', 'note': 'search failed 3x',
                                 'tries': tries}
                    print('    confirmed buyer - 3 tries exhausted, set aside for review')
                else:
                    done[kid] = {'status': 'retry-buyer', 'note': 'search found no site',
                                 'tries': tries}
                    print('    confirmed buyer - re-queued (try %d)' % (tries + 1))
            else:
                done[kid] = {'status': 'no-match'}
        state['processed'] = done
        json.dump(state, open(STATE, 'w'), indent=2, ensure_ascii=False)

    # anything still buffered (a row built but not yet appended) is saved
    # here too, so nothing written while we worked is lost
    if new_rows:
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
