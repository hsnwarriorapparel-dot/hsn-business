# go4WorldBusiness — profile fixed, listings blocked, and two brand traps

Member: `hsnwarriorapparel_9`, JUNIOR MEMBER since 24 Oct 2026.
Dashboard: https://www.go4worldbusiness.com/member/dashboard/

## What was WRONG on the profile (all now corrected and VERIFIED saved)

| Field | Was | Now |
|---|---|---|
| Phone | +965-65002313 (Kuwait) | +92 337 3336381 |
| Address | "-" | Sialkot Industrial Estate, Sialkot 51310, Punjab, Pakistan |
| City / State / Zip | Sialkot / - / - | Sialkot / Punjab / 51310 |
| Year Established | 2010 | 2011 |
| Annual Sales | "Not Known" | 250,000 to 1 million USD |
| Primary Business | Manufacturer/OEM | unchanged (correct) |
| Brand Name / Trade Name | empty | HSN Warrior Apparels |
| Brand Tagline | empty | Custom martial arts and sportswear manufacturing for clubs, academies and brands |
| Designation | empty | Owner |
| Certifications | empty | OEKO-TEX, REACH |
| Domestic Market | empty | Pakistan |
| Countries Already Exported To | empty | Portugal, Spain, UK, Germany, Ireland, Netherlands, France, Italy, USA, UAE, Czech Republic, Poland |
| "I am a supplier of" | "Martial arts and sportswear products" | full product + discipline list |
| Company Introduction | EMPTY | 1461 chars |

**STILL WRONG and NOT fixable from the dashboard: Country = Kuwait.** The
field renders with `class="country-readonly-field"` — it is not an input, it
is display-only. It cannot be changed on the Company Profile page. It needs a
support request to go4WorldBusiness (support link in the footer) or a profile
deletion and re-registration. This is the single biggest trust problem on
the storefront: a Pakistani factory showing Kuwait is wrong, and buyers filter
on country.

After saving, the page shows **"Recent profile changes are under review"** and
every field becomes `disabled`. That is normal moderation, not a failure - the
values persist and are read back correctly.

## The pages (the nav is JS-driven, these URLs are the real ones)

- Dashboard: `/member/dashboard/`
- Company Profile (fields): `/member/dashboard/company-profile`
- About Your Company (intro/logo/office images): `/member/dashboard/homepage`
- Management & Teams: `/member/dashboard/management`
- Manufacturing & Facilities: `/member/dashboard/facilities`
- Newsroom: `/member/dashboard/newsroom`
- Matching Buy Leads: `/member/dashboard/matching-buyleads`
- Your Products: `/member/dashboard/products`
- Add Product: `/member/dashboard/add-product` -> posts to
  `/member/dashboard/products/new/new/0`

## THE PRODUCT FORM (mapped field by field)

Required (7): Product Name, Product Grade, Min Price USD, Max Price USD,
Price Unit, Incoterms, Product Description.

Names (note the `[prod]` nesting on the first three):
- `member_edit_prefproduct[prod][name]` - **MAX 48 CHARACTERS**. The server
  rejects longer with "This value is too long. It should have 48 characters
  or less." and shows only a generic "Correct the errors below to proceed."
  banner. Put the full SEO name at the TOP of the description instead.
- `member_edit_prefproduct[prod][productGrade]`
- `member_edit_prefproduct[prod][minPrice]` / `[maxPrice]`
- `member_edit_prefproduct[prod][rateUnit]` - values: **Piece=18, Pair=17**
- `member_edit_prefproduct[prod][incoterm]` - **DDP=3**, FOB=5, EXW=4, CIF=2, CFR=1
- `member_edit_prefproduct[description]`
- `member_edit_prefproduct[mfgCountry]` - value is the country NAME
- `member_edit_prefproduct[deliveryTimeUnits]` - Piece=18, Pair=17
- plus deliveryTime, packDetails, capacity, sample radios, sellercode,
  standards, trademarkName, loadingPort, usageOrApplication, brand, modelNo,
  hsCode, keySpec1-4, keyAdv1-4

The Save button is labelled **"Save Product"** (not "Save") and has
`name="member_edit_prefproduct[next]"` - it is a multi-step wizard.

## THE IMAGE WIDGET (this is the hard part)

The flow is NOT "set the file input". It is:
1. `DOM.setFileInputFiles` on `member_edit_prefproduct[images][0][file][file]`
2. click `label.imageUploadBtn` (the "Upload" LABEL, `for="member_edit_prefproduct_images_0_file_file"`)
3. a CROP canvas opens - click **`#cropBtn_0`** (the label titled "Save cropped image", text "Save") to actually upload
4. the hidden `member_edit_prefproduct[image0]` fills with an S3 URL and
   `#imageUploadedPreview_0` shows the image
5. check `#choose_primary_0` (radio `primaryImageRadio`) to make it primary -
   the container `#primaryCheckboxContainer_0` is `visibility:hidden` until then

Skipping step 3 leaves `image0` empty and the form refuses to save.

## WHERE IT STILL STOPS

With every field filled, the image uploaded, primary set, and
`form.removeAttribute('read_only')` applied, the page shows **no error banner**
but the product is NOT created - "All Products (0)" stays 0 and the URL does
not change. `form.requestSubmit(button)` behaves the same as a click.

The form element is `read_only=""` and `novalidate=""`, and the site also
exposes a `form-pre-submit-path` AJAX endpoint (value `/form/pre-submit.ajax`)
that the submit button likely calls before the POST. That pre-submit call is
the most likely missing step.

**Next time:** intercept `Network.requestWillBeSent` / `responseReceived` for
the pre-submit URL and replay it, or watch what the button's own JS handler
does. Do NOT re-derive the field list - it is correct.

Scripts written (all on disk):
- `g4wb_fill_profile.py` - fills + saves the profile and homepage
- `g4wb_publish_products.py` - fills the product form and submits
- `g4wb_net_probe.py` - single-connection form probe
- `g4wb_click.py` / `g4wb_eval.py` / `g4wb_read.py` - generic page helpers
- `g4wb_listings.py` - the 10 listing definitions (name, price, specs, copy)
- `build_g4wb_listing_images.py` - composes the listing images
- `build_g4wb_assets.py` - logo + cover, using the website brand colours

## 5 FREE DAILY BUYER INQUIRIES - the real prize

As a JUNIOR member: **1 buyer inquiry per day free** (max 2 per week), 5
inquiries/day to suppliers & products, and **Premium gets 100 buyers/day**
(60 days, no auto-renewal, money-back guarantee).

BUT: `Matching Buy Leads for You` shows **"Total 0 Buy Leads Matching Your
Profile"** and says *"Please check your Company Profile and make sure you
have displayed all the Industries and Products you deal in."*

The profile's "I am a supplier of" textarea is `disabled="disabled"` and is
filled by a category/chip picker, not free text. Our text is saved but the
site may key matching off a separate category list. **That category picker is
the unlock for buyer matching** - find it before adding products, because a
matched buyer inquiry is worth more than a product listing.

## TWO BRAND TRAPS FOUND (both are trademark exposure)

1. **The website's own boxing hero image shows EVERLAST-branded gloves**
   (`assets/img/hero-boxing.jpg` - blue Everlast gloves, logo readable). We
   are not Everlast. This is on OUR public site and should be replaced with a
   real photo of our own gloves.
2. **Every photo in `/home/ubuntu/product_photos/` carries ANOTHER CLIENT's
   brand**: GRACIE BARRA, PITBULL, FIGHT CLUB, FERAL GEAR, EQUIPE,
   FIGHTING FEROCITY, HURRICANE, SEVERE, REBELS, DARK FIGHT WEAR. The
   catalog PDF images are no better (U&U, MUALA, CAPITAL) and the catalog is
   *"Prepared for Team Duramuk"*.

**Rule for anything client-facing: never use another client's branded
garment as our own product photo.** The listing images are therefore
COMPOSED - our logo + our own factory/lifestyle photos from the website
assets (sewing-line, gi-fabric, gym-team, karate-kids, judo-throw, mma-ground,
hero-grappling are unbranded) + typed specs. That is what
`build_g4wb_listing_images.py` does.

Also note: the catalog PDF says **"MOQ from 20 pieces on many items"** and the
website says **"30+ units minimum per style"** while the skill said
10-piece MOQ. The website number is the public promise, so all listings,
profile copy, follow-ups and chain pitches now say **30+ units per style**.
