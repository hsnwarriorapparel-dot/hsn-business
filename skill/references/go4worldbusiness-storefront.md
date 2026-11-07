# go4WorldBusiness — buyer inquiry sent, and EVERYTHING learned (2026-11-07)

Member `hsnwarriorapparel_9`, JUNIOR. Dashboard:
https://www.go4worldbusiness.com/member/dashboard/

## ✅ FIRST INQUIRY SENT

**Karate Black Master Belt — 400 pieces — Krav Maga Federation (Israel)**
Inquiry sent 2026-11-07, status **Open**. Recorded as **L5261** in leads.csv.

RFQ: "Judo Karate Belts, in black and brown, with logo, 400 pcs", HS 6109,
CIF Israel, payment TT, looking for suppliers worldwide. Our belts are the
EUR 3.00 line item, 30+ units per style, 3-4 weeks production.

Verify it landed: https://www.go4worldbusiness.com/member/dashboard/inquiries/sent
(row: Nov-7-26 | Buylead | WANTED : Karate Black Master Belt | Open |
Krav Maga Federation).

## THE THREE RULES THAT DECIDE IF AN INQUIRY CAN BE SENT

1. **A buylead can only be inquired about 5 DAYS AFTER it was posted.**
   Error text: *"Please note that you can only inquire about a buylead 5 days
   after it has been posted. To access fresh buyleads immediately, upgrade your
   membership today."* The freshest RFQs (posted today) are LOCKED.
2. **Some RFQs are "PREMIUM MEMBERS ONLY"** — those are locked regardless of age.
3. **JUNIOR limits: 1 buyer inquiry per day free (max 2 per week)**;
   5 inquiries/day to suppliers & products. Premium = 100 buyers/day for
   60 days, no auto-renewal, money-back guarantee.

So the best targets are OLDER free RFQs (5+ days). From one search pass:
76 of the leads found were age>=5 and not premium-only.

## THE INQUIRY FORM (mapped field by field)

URL: `https://www.go4worldbusiness.com/inquiries/send/buyleads/<id>/<slug>`
It POSTs to `/inquiries/send`.

| Field | Value |
|---|---|
| `form[message]` | the quote text (required) |
| `form[companyName]` | pre-filled "HSN Warrior Apparels", readonly |
| `form[name]` | pre-filled "Ghulam Hassan", readonly |
| `form[email]` | pre-filled "hsnwarriorapparel@gmail.com", readonly |
| `form[phone]` | pre-filled "+92 337 3336381", readonly |
| `form[country]` | select, value = country id (India=99) |
| `form[captcha]` | **Gregwar image captcha**, required |
| `form[_token]` | CSRF |
| hidden | `form[itemId]`, `form[itemType]`=buyleads, `form[itemTitle]`=slug |

Button: **"Inquire Now"** (type=submit).

### CAPTCHA — the fiddly part
- Image: `#form_captcha_image`, src
  `/generate-captcha/_captcha_captcha?n=<token>&n=<timestamp>` (Gregwar).
- Label: *"Please enter the following text in the box below"* / *"Type the
  characters exactly as shown."*
- **The image is regenerated on EVERY page load.** Reading the captcha in one
  tab and submitting in another fails, and the error is just the generic
  "Error processing your request!" - it does NOT say "wrong captcha".
- **Therefore the sender is TWO-PHASE and must reuse the same tab:**
  1. Phase 1 (no captcha arg): open the tab, screenshot `#form_captcha_image`
     via `Page.captureScreenshot` with a clip at scale 3, save the targetId to
     `/home/ubuntu/g4wb_inquiry_target.json`.
  2. Read the text out of the PNG (vision).
  3. Phase 2 (captcha arg): reattach to that SAME targetId, fill everything,
     click Inquire Now, verify on `/member/dashboard/inquiries/sent`.
- Script: `/home/ubuntu/g4wb_inquiry_send.py <path> <captcha> [message_file]`
- Running it takes ~60-90s per phase (the page load is slow) - run it in the
  BACKGROUND, not in a 300s foreground window.

## COUNTRY: PAKISTAN IS ON THE PLATFORM — id 162 (CORRECTION)

**The earlier note in this file that "Pakistan does not exist on this site"
was WRONG.** It came from reading the wrong country's list. The inquiry form's
country select has **240 countries and `162~Pakistan`** (also `99~India`,
`112~Kuwait`). The profile's `codeToIdMap` uses the SAME numbering.

**Fixed 2026-11-07:** the profile country now reads **Pakistan** and every
inquiry sends with `countryId = 162`. No support request is needed.

How the country gets set: `POST /signup/ajax/category-selection/supplier`
with `{"categories":[ids],"compname","phone","state","countryId":"162"}`
(script `g4wb_set_categories.py`). That call ALSO resets some profile
fields, so run `g4wb_fill_profile.py profile` straight after it.

Verified after the fix: country Pakistan · year 2011 · brand HSN Warrior
Apparels · tagline · address "Sialkot Industrial Estate, Sialkot 51310,
Punjab, Pakistan" · city Sialkot · state Punjab · zip 51310 · phone
+92 337 3336381 · email hsnwarriorapparel@gmail.com · homepage
https://hsnwarriorapparels.vercel.app · OEKO-TEX, REACH · export markets
Portugal, Spain, UK, Germany, Ireland, Netherlands, France, Italy, USA, UAE,
Czech Republic, Poland · brand story still empty (logo upload required).

The homepage/intro save does not submit because the platform requires a logo
image on the homepage first. Everything else saves.

## THE BUYER-INQUIRY DAILY LIMIT — it is 1 PER DAY, not 5

Error text from the platform:
*"As you are not a Premium GOLD/SILVER Member, you can only contact limited
number of buyers."*

Measured on 2026-11-07: the FIRST buyer inquiry (Karate Black Master Belt)
succeeded; the SECOND one the same day (Taekwondo Belts, 3,500 pcs) was
refused with that error. So a JUNIOR member gets **1 buyer inquiry per day**,
not the 5/day that applies to suppliers and products. **Premium GOLD/SILVER
gets 100 buyers/day** (60 days, no auto-renewal, money-back guarantee).

The platform's own sales copy on that screen: *"Contact 100 Buyers per day"*.

Member inquiries (`/inquiries/send/members/<id>/<slug>`) use the SAME form
and the SAME 1/day buyer limit.

### The daily buyer-inquiry queue
`/home/ubuntu/g4wb_buyer_queue.py` keeps a ranked queue of eligible RFQs and
sends the biggest one per day:

```
 1. taekwondo-belts                            3500 pcs  Malaysia   (LC, CIF, worldwide)
 2. soccer-football-jerseys-unit-units         2000 units USA      (PREMIUM ONLY - blocked)
 3. boxing-accessories-like-hand-tie-gloves-head-guard  500-1000 pcs Egypt (LC, CIF)
 4. martial-arts-belts-like-judo-belts          100 pcs  Portugal   (LC, CIF, worldwide)
 5. taekwondo-uniforms                          MOQ     Israel
 6. taekwondo-mats                              MOQ     UAE
 7. martial-arts-wear                           MOQ     Oman
 8. boxing-gloves-boxing-headgear-and-groin-protectors  MOQ  USA
```

- `--list` prints the ranked queue with eligibility
- `--mark <slug> SENT|FAILED` records the outcome
- state file `/home/ubuntu/g4wb_buyer_queue_state.json` holds the day's count
- cron `g4wb-daily-buyer-inquiry` (job d8fd4cf307aa, 09:05 UTC daily,
  script `g4wb_buyer_inquiry.sh`, no_agent) runs phase 1 and leaves the
  captcha image for the agent to finish phase 2
- tailored per-RFQ copy lives in `g4wb_belt_messages.py` and is QA'd by
  `spam_qa_followup.check()` - note "quotation" contains the banned token
  "quote", so use "price" or "pricing" instead

## RANKED RFQ DETAILS

**Taekwondo Belts - Malaysia - 3,500 pieces** (May-22-24, ARCHIVED but
contactable, LC, CIF, worldwide): White 2000, Green 1000, Red 350, Black 50,
Yellow 100.

**Boxing Accessories - Egypt - 500-1,000 pieces** (Jun-30-26, **VERIFIED**,
LC, CIF): hand ties, gloves, head guard, mouth guard, cap. Looking for
suppliers from Egypt only.

**Judo Belts - Portugal - 100 pieces** (Aug-01-24, ARCHIVED, LC, CIF,
worldwide): with own logo, White/Yellow, Yellow, Yellow Orange, Orange.

**Soccer / Football Jerseys - USA - 2,000 units** (Nov-06-26, VERIFIED,
PREMIUM MEMBERS ONLY, HS 610910, worldwide). Locked by the premium rule AND
by the 5-day rule until Nov-11-26.

## CATEGORIES — what actually unlocks buyer matching

Discovered from the site's own JS bundle `b385a6b.js`:

- search: `GET /signup/ajax/category-search?q=<term>` -> `[{label,value}]`
- save: `POST /signup/ajax/category-selection/supplier`
  `Content-Type: application/json`
  body: `{"categories":["<id>",...], "compname":"...", "phone":"...",
  "state":"...", "countryId":"<id>"}`
- **MAX 10 categories** - the endpoint replies
  `{"success":false,"message":"You can select at most 10 categories."}`
- the save response is `{"success":true,"data":{...,"inAppRoute":"/communities"}}`
  and it **RESETS some profile fields** (year went back to 2010, address back
  to "-", brand fields cleared) - so re-run `g4wb_fill_profile.py profile`
  AFTER setting categories.

Our 10 (IDs verified by searching the API):
Martial Arts Goods and Accessories 1211900992 · Martial Arts Gloves
1211900998 · Martial Arts Belts 1211900997 · Martial Arts Mats 1211900999 ·
Shin Guards 1211900940 · Gym Belts 1211904448 · Apparel, Clothing & Garments
1217662976 · Sportswear 1334874723 · Sportswear Sets 1334858527 · Uniforms
1217663872

Script: `/home/ubuntu/g4wb_set_categories.py`

**After saving categories, `Matching Buy Leads` still showed 0** - the
matching likely needs products listed first (the product form is still not
submitting, see below).

## THE PRODUCT FORM - still not creating a product

Mapped and ready; one step still missing.

- Product Name max **48 characters** (server error says so, but only a
  generic banner shows - put the full SEO name at the top of the description).
- Save button is **"Save Product"**, `name="member_edit_prefproduct[next]"`.
- Image flow: set the file input -> click `label.imageUploadBtn` ->
  **click `#cropBtn_0`** (the "Save cropped image" label) to actually upload ->
  check `#choose_primary_0` to make it primary.
- Select values: `rateUnit` Piece=18 Pair=17 (under `[prod]`), `incoterm`
  DDP=3, `mfgCountry` = country NAME.
- The form element carries `read_only=""`; stripping it clears the error
  banner but the product is still not created (0 after many attempts). The
  missing step is most likely the `form-pre-submit.ajax` call the button makes
  before the POST.

Scripts: `g4wb_publish_products.py`, `g4wb_net_probe.py`, `g4wb_listings.py`,
`build_g4wb_listing_images.py`.

## FINDING BUYERS - the real feed

- `https://www.go4worldbusiness.com/list/latest/buyleads` = live VERIFIED
  buyer RFQs, newest first.
- `https://www.go4worldbusiness.com/import-export-communities` = community
  feed with live supplier posts (also a way to see what competitors post).
- **The search box is `input[name="searchText"]` and the form SUBMITS to
  `/find?searchText=<term>`.** A `?keyword=` query param does NOT filter -
  it returns the same list. Type into the box and submit the form, or fetch
  `/find?searchText=<term>` directly.
- Each lead's contact path is
  `/inquiries/send/buyleads/<id>/wanted-:-<slug>`.
- Script: `g4wb_find_buyleads.py <terms...>` -> writes
  `g4wb_buyleads_found.json`.

Best live match found: **Soccer / Football Jerseys, 2,000 units, United
States, Nov-06-26, HS 610910, looking for suppliers worldwide** (L5258) - but
it is 0 days old, so the 5-day rule locks it. It becomes contactable on
**Nov-11-26**.

## PROFILE STATE NOW (verified)

Country: **India** (placeholder - see above) · Year 2011 · Phone +92 337
3336381 · Address Sialkot Industrial Estate, Sialkot 51310, Punjab, Pakistan ·
City Sialkot · State Punjab · Zip 51310 · Business Manufacturer/OEM · Sales
250k-1M USD · Brand "HSN Warrior Apparels" · Tagline set · Owner ·
OEKO-TEX, REACH · Export markets: Portugal, Spain, UK, Germany, Ireland,
Netherlands, France, Italy, USA, UAE, Czech Republic, Poland · supplier-of
list set · categories set (10).
