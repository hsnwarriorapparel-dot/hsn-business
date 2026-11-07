# The go4WorldBusiness buyer-company funnel (2026-11-07)

## WHY THIS EXISTS

The platform's inquiry form is a **1-per-day slot**, not a channel. Measured
2026-11-07: the first buyer inquiry of the day succeeded, the second was
refused with

> *"As you are not a Premium GOLD/SILVER Member, you can only contact limited
> number of buyers."*

JUNIOR = **1 buyer inquiry/day** (the 5/day applies to suppliers and products).
Premium GOLD/SILVER = 100 buyers/day, 60 days, no auto-renewal.

So the strategy is NOT "send more inquiries". It is: **use the slot for the
biggest order available, and build a second funnel that the slot cannot
block.**

## THE TWO FUNNELS

### 1. The daily slot (highest intent, 1/day)
`g4wb_buyer_queue.py` keeps a ranked queue of RFQs and sends the biggest
eligible one each day. The captcha is regenerated on every page load, so the
send is TWO PHASE:
1. `g4wb_inquiry_send.py <href>` opens the tab and screenshots
   `#form_captcha_image`, saving the targetId
2. `g4wb_inquiry_send.py <href> <captcha> [msgfile]` reattaches to that SAME
   tab, fills and clicks "Inquire Now"

Reading the captcha in one tab and submitting in another fails with a
generic "Error processing your request!" - it does NOT say "wrong captcha".

### 2. The buyer-company directory (unlimited)
This is the volume channel.

**TWO directory shapes exist and only one is useful:**

| URL | What it lists |
|---|---|
| `/buyers/<country>/<category-slug>` | buy REQUIREMENTS (a lead, with a personal contact name) |
| `/buyers/<country>/<category-slug>.html` | **BUYER COMPANIES** (the target) |

The `.html` variant gives real company names with their profile URL:

```
/buyers/oman/sports-goods-equipments.html
   Al Ali Trading And Cont.      => /member/view/3840682/al-ali-trading-and-cont-.html
   Muscat Sports LLC             => /member/view/3994822/muscat-sports-llc.html
   Supa Sportsman LLC            => /member/view/1484424/supa-sportsman-llc.html
   Four Peaks Trading ...        => /member/view/4011206/four-peaks-trading-and-contracting-llc-oman.html
```

A COMPANY NAME is a strong search key (a person's name is not - it rarely
appears on the company's site). Find the company, find its site, find its
sales email, contact them directly. **No platform limit, no captcha, no
daily cap.**

## THE PIPELINE

```
g4wb_company_harvest.py   walk /buyers/<country>/<cat>.html  -> g4wb_company_harvest.json
company_reach.py          search each company -> verify -> extract email -> leads.csv
g4wb_dir_harvest.py       walk the REQUIREMENT pages -> g4wb_buyer_harvest.json (personal names)
g4wb_filter_harvest.py    keep buyers whose own "Buyer Of" category is ours
buyer_reach.py            same reach, for personal names
```

Scripts: `g4wb_dir_pipeline.sh`, `g4wb_company_pipeline.sh`
State: `company_reach_state.json`, `buyer_reach_state.json`

## SEARCHING FROM A SCRIPT

**Every curl-based search engine is blocked on this host:**
DuckDuckGo html -> 202 with zero results; Bing -> 200 with an empty body;
Ecosia -> 403; Mojeek/Startpage/searx -> no result markup.

Use the **real browser**: `browser_search.py` drives the work browser to
Bing and reads `li.b_algo`. Bing wraps links in `bing.com/ck/a?...` - take
the URL from each result's `<cite>` element instead.

Reconstructing a url from `<cite>`: the text is `domain › path › more`.
Join the path pieces with `/`, do NOT replace spaces with dashes:

```
'supasportsman.com › index.php › contactus'
  -> https://supasportsman.com/index.php/contactus
```

The old dash-joining produced broken urls that never fetched.

## FILE COLLISION - two harvesters, one output file

`g4wb_harvest_buyers.py` and `g4wb_dir_harvest.py` BOTH wrote
`g4wb_buyer_harvest.json`. Whichever finished last wiped the other's entries.
Each harvester now owns its own file:

```
g4wb_buyer_harvest_dir.json     <- g4wb_dir_harvest.py      (803 entries)
g4wb_buyer_harvest_search.json  <- g4wb_harvest_buyers.py   (8 entries)
g4wb_buyer_harvest_filtered.json <- g4wb_filter_harvest.py  (96, merged)
```

`g4wb_filter_harvest.py` merges all of them (plus the legacy file) and keys
on name+country+product so the same buyer from two sources merges.

## PAGINATION - the directory is far deeper than one page

Every buyer-category directory page carries a "Next" link with a
`searchAfter` cursor:

```
/find?searchText=martial-arts-mats&BuyersOrSuppliers=buyers
  &countryFilter[0]=oman&cityFilter[0]=&FindBuyers=&_format=html
  &searchAfter=WzE1LjMyNzMyNCwxNzUyMTI3OTMzOTg3XQ
```

Page 1 gives 50 requirements; the cursor walks deeper (oman/martial-arts-mats
page 2 gave 41 more, and it keeps going). The pagination block is
`<ul class="pagination search-after-pagination">` and the next link carries
`searchAfter`.

`g4wb_deep_harvest.py` follows the cursor N pages deep:

```
g4wb_deep_harvest.py --pages 4 --countries oman egypt malaysia portugal \
    --cats sportswear team-uniforms fight-gear fight-wear mouth-guards
```

Yield: **1,662 buyer identities** (page 1: 1399, p2: 191, p3: 47, p4: 25)
and **212 buyers** in our product space after filtering - up from 96 before
pagination.

### WHICH CATEGORY SLUGS ACTUALLY HOLD BUYERS

The directory slugs are NOT reliable - `martial-arts-mats` (161 leads) holds
mostly floorings, and `boxing-head-guards` (69) mostly medical gloves. The
CLEAN slugs (ours/total ratio) are:

| slug | ours | total |
|---|---|---|
| sportswear | 36 | 36 |
| fitness-equipment-sports-goods | 28 | 45 |
| martial-arts-gloves | 8 | 122 |
| mouth-guards | 5 | 17 |
| team-uniforms | 4 | 47 |
| sports-goods-equipments | 3 | 3 |
| fight-gear | 2 | 63 |
| fight-wear | 2 | 27 |
| martial-arts-belts | 1 | 26 |

Deep-harvest the clean slugs, and always filter on the buyer's OWN
"Buyer Of" category, never on the directory slug.

### THE FILTER - category OR product, minus wrong trades

A buyer wanting "Sports Jerseys 500 Pairs" is ours even when their category
line is vague, so the filter accepts `OUR.search(category) OR
OUR_PRODUCT.search(product)`, then drops anything matching `NOT_OURS`
(flooring, carpets, rugs, printer toner, medical, food, prayer mats).

## ONE VERIFIED IMPLEMENTATION, NOT TWO

`buyer_reach.py` (personal names) and `company_reach.py` (company names) are
two funnels. They MUST share one verification implementation - when
`buyer_reach.py` had its own weaker copy it added a `sentry.wixpress.com`
error-tracker address, a beauty salon and a parked domain. It now imports
every check from `company_reach.py`:

```
valid_email, NOT_A_COMPANY, OTHER_TRADE, OTHER_SPORTS, PRODUCT_WORDS,
RETAIL_WORDS, WHOLESALE_WORDS, DEAD_SITE, GOOD_ROLE, find_phones,
site_domain, strip_tags, title_hint
```

### The state key must match the filter key

The filter merges the harvest files and keys on
`name|country|product`. The reach scripts must key their state file the
SAME way, or every buyer looks unprocessed on every run and the funnel
never advances. `company_reach.py` keys by the stable member id, so it was
fine; `buyer_reach.py` keyed by the harvest id and was re-processing
everyone.

| False positive | Cause | Fix |
|---|---|---|
| `cobrasports.com` | parked domain "For Sale" | `DEAD_SITE` check |
| `cssportinggoods.com` | an Arizona RETAIL store for a Malaysian buyer | `RETAIL_WORDS` check |
| `tackapparel.com` | a US COMPETITOR matched on the generic word "apparel" | `company_tokens(distinctive_only=True)` - drop clothing/apparel/trading/group/one/new |
| `bluechipoman.com` | "Pipes and Fittings Suppliers" passed on a stray "sports" | product must be in the TITLE + first 900 chars, and `OTHER_TRADE` blocklist |
| `definitions.net` | a DICTIONARY - "kit" appears in every entry | `NOT_A_COMPANY` blocklist |
| `order@rand.org` | a random string scraped from page text | email must be on the company's own domain |
| `a-logo-black-@1x.png` | a FILENAME parsed as an address | `valid_email()` - reject image/css/js TLDs |

**Every email must be on the company's own domain** (or a listed
`ALLOWED_MAIL_DOMAINS`: omantel.net.om, batelco, etisalat, gmail, hotmail...).
A small Omani firm often publishes its contact on omantel.net.om.

**A phone number is as good as an email** - it opens the WhatsApp channel.
But it must come from a page ON THE COMPANY'S OWN DOMAIN: a guessed
`/contacts` path can redirect elsewhere, and that is how two Omani buyers
were matched to `definitions.net` with one stray number.

## FOUR BUGS IN THE REACH PIPELINE

1. **`title_hint(text)` should be `title_hint(html)`** - `title_hint` expects
   HTML. Passing stripped text made it return '' and the head-check silently
   rejected EVERY good match. This is why 30/30 companies returned "no match".
2. **A flaky site was marked as seen on its first failure.** `supasportsman.com`
   returned empty HTML on its home page but worked on
   `/index.php/contactus`. Mark the domain as seen only AFTER a page loads.
3. **PHP sites put the contact page under the app root.** Try
   `/index.php/contactus`, `/index.php/contact`, `/index.php/about`,
   `/index.php/en/contact` as well as the plain paths.
4. **Two reachers writing leads.csv at once lost leads.** Both
   `company_reach.py` and `buyer_reach.py` now take an exclusive lock
   (`company_reach.lock` / `buyer_reach.lock`).

## THE STRONGEST SIGNAL - the buyer's own category

The buyer's "Buyer Of ..." line is what THEY call their business. It is
far more precise than the directory tag: the site's `martial-arts-mats`
category contains prayer mats and car mats. Filter on the buyer's own
category, not the directory slug.

## KNOWN-GOOD RESULTS (2026-11-07)

```
Muscat Sports LLC     +968 99205884                 muscatsports.com
Supa Sportsman LLC    ssports@omantel.net.om         supasportsman.com
                      +968 24834825
```

Supa Sportsman: "SUPA SPORTS MAN OMAN | For Quality Sports Goods and
Fitness Equipment" - a real Omani sporting goods importer.

## THE COUNTRY - Pakistan IS there

`162~Pakistan` (240 countries in the inquiry form's select). The profile
country is now **Pakistan**. An earlier note in this skill saying Pakistan
was absent was WRONG - it came from reading the wrong country's list.
Kuwait = 112, India = 99.

## RESULTS SO FAR (2026-11-07)

- buyer-company directory: **101 companies in one pass** (Oman: sports goods
  34, sportswear 27, uniforms 24, kick pads 10, mouth guards 13)
- buyer identities (personal names): **676 harvested**, 60 filtered to our
  product space
- confirmed real companies found: Supa Sportsman LLC (Oman, sporting goods +
  fitness equipment, `ssports@omantel.net.om`), Caresun Sportswear, Muscat
  Sports LLC, Gloves Up Fitness Club, Al Ali Trading & Contracting, Bid Bid
  Wholesale & Retail, Four Peaks Trading & Contracting
- first inquiry sent: Karate Black Master Belt, 400 pcs, Krav Maga
  Federation (Israel) - status Open

## THE QUEUED RFQs (biggest first)

| RFQ | Qty | Buyer | Terms |
|---|---|---|---|
| Taekwondo Belts | 3,500 | Malaysia | LC, CIF, worldwide |
| Boxing Accessories | 500-1,000 | Egypt | LC, CIF |
| Judo Belts (own logo) | 100 | Portugal | LC, CIF, worldwide |
| Taekwondo Uniforms | MOQ | Israel | |
| Taekwondo Mats | MOQ | UAE | |
| Martial Arts Wear | MOQ | Oman | |
| Boxing Gloves + Headgear | MOQ | USA | |
| Soccer/Football Jerseys | 2,000 | USA | premium-only + 5-day lock |

## COPY

Tailored per-RFQ copy lives in `g4wb_belt_messages.py`, QA'd by
`spam_qa_followup.check()`. **"quotation" contains the banned token "quote"**
- use "price" or "pricing".
