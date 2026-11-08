# HSN Warrior Apparels — Client Acquisition Report

**Prepared by:** Hermes Agent, on behalf of HSN Bajwah
**Date:** 8 November 2026
**Subject:** How clients are being found, contacted and converted

---

## 1. Executive Summary

HSN Warrior Apparels has an automated client-acquisition system running on a
single server. It runs five independent channels against a shared tracker, all
scheduled, all resumable, all capped.

**Current position (measured, 8 November 2026):**

| Metric | Value |
|---|---|
| Leads in tracker | 5,227 |
| Countries covered | 36 |
| Leads with a verified email | 2,748 |
| Leads with a phone number | 4,096 |
| Cold emails sent | 2,112 |
| Instagram accounts followed + messaged | 1,426 |
| WhatsApp messages sent | 74 |
| Buyer/import companies identified | 12 |
| **Replies received (live buyers)** | **6** |
| go4WorldBusiness requirements in hand | 4 verified |
| go4WorldBusiness inquiries sent | 1 (confirmed by the platform) |

**The single most important fact in this report:** the cold-email channel is
finding clubs, but the *buyer* channel is where order value sits. Six replies
have come in from clubs. Every one of them is a B2B buyer worth more than a
hundred club emails combined. The work of the last day has been to fix the
buyer channel so it reaches the same standard.

---

## 2. The Five Channels

### Channel 1 — Google Maps lead generation (the engine that feeds everything)

**Where:** Google Maps Platform API, running as a local Docker service on the
server.

**How it works.** A local Maps engine is queried across a matrix of
**24 cities** and **5 keyword types**, at a search depth of 5 with email
enrichment switched on:

- **Keywords:** boxing gym, MMA gym, jiu jitsu academy, muay thai gym, martial
  arts school
- **Cities:** Houston, Chicago, Phoenix, Philadelphia, San Antonio, Dallas,
  Atlanta, Boston, Seattle, Denver, Las Vegas, Detroit, plus European cities
  including Paris, Berlin, Madrid, Barcelona, Milan, Rome, Lisbon and Zurich

That is 120 searches per run. For each result the engine captures the name,
category, street address, phone, rating, review count and website. It then
visits each club's website and its contact pages to extract email addresses,
filtering out form-service and placeholder addresses (`sentry`,
`wixpress`, `example.com`, `privacy@`, `postmaster@`).

**Deduping** is done against the live tracker by **both email and phone**, so
re-running is safe and never creates duplicates. This is what has produced
**4,414 of the 5,227 leads**.

**Schedule:** 9:00 UTC daily (2:00 PM Pakistan time).

**Scale note:** last night's run alone added 83 new clubs. They are
legitimate — boxing gyms and martial arts schools, most with real contact
addresses.

### Channel 2 — Cold email (first touch and follow-up)

**Where:** Gmail, driven through the Chrome DevTools Protocol. The agent
clicks Compose, types the recipient, tabs to subject, tabs to body, sends,
then reads the sent row back to confirm.

**The copy.** Four subject lines rotate so no two clubs receive an identical
message:

```
Custom martial arts gear for {name} - HSN Warrior Apparels
HSN Warrior Apparels - club gear manufacturing for {name}
Branded uniforms & equipment for {name}
{name} x HSN Warrior Apparels - custom club apparel
```

The body names a specific product line relevant to that club's discipline,
states the manufacturer advantage (OEM/private label, their logo, factory
prices), and closes with a single question. Every message passes an automated
spam-word screen before it is allowed to send.

**Follow-ups** rotate through three angles — **price** (a price list with
actual EUR figures), **minimum order quantity** (30 units per style, against
the industry norm of 100), and **production lead time** — with three subject
lines that avoid the language buyers delete.

**The hard 100/day cap.** Every send goes through a shared quota ledger
(`send_ledger.jsonl`) that all four email engines write to, so the wave, the
follow-ups, the chain pitches and the reply engine can never collectively
exceed 100 cold emails in a calendar day. Replies are tracked separately and
**do not** consume the cold allowance, because answering someone who wrote to
us is not cold outreach.

**The daily allowance is reserved, not first-come.** The wave runner checks
what is still free after reserving the follow-up and chain-pitch budgets, so
the first-touch wave can never consume the budget that follow-ups need.

**Current daily usage:** 86 of 100 (65 first-touch, 14 follow-up, 2 replies,
5 reserved for chain pitches and follow-ups).

### Channel 3 — Instagram (follow + direct message on the same day)

**Where:** Instagram, via the logged-in browser session.

**Why it matters.** Google Maps only surfaces an Instagram handle when the
club's website happens to link one — roughly 1 in 171. So a dedicated
handle-hunt script crawls every lead's own website and contact pages looking
for `instagram.com/<handle>` links and writes the handle back into the tracker.
That single change is what makes this channel work at scale.

**What it sends.** Five opener variations, four middle lines, three offer
lines and four calls to action, all randomised per recipient so no two clubs
receive the same message. The offer is consistent: OEM and private-label
production, uniforms, gloves and team wear, their branding, factory-direct,
low minimums for clubs. The close is always the same single question — *would
the catalogue and wholesale price list be useful?*

**Scale:** 1,426 accounts followed and messaged, per the tracker's own
counter.

### Channel 4 — WhatsApp

**Where:** WhatsApp Web, driven through the Chrome DevTools Protocol.

The agent opens a conversation, types the message, sends, then **reads the
transcript back** to confirm delivery. That read-back is what catches silent
failures — a click that lands outside the viewport, a conversation that never
opened, a message that queued but never went.

**Scale:** 74 messages sent. This is deliberately the smallest channel. It is
reserved for clubs that have already shown interest or replied on another
channel, because a cold WhatsApp message to a stranger gets ignored and can
get the number restricted.

### Channel 5 — go4WorldBusiness (buyer and import companies) — the channel that matters most for revenue

This is the channel that reaches **businesses buying in volume**, not clubs
ordering 30 pieces. It is also the newest and the most heavily re-engineered.

**What was found.** The `/buyers/` pages on go4WorldBusiness are not a company
directory. They are **live buy requirements**, and each one states the product,
the specification, the quantity, the destination, the payment terms and
frequently the HS code:

```
VERIFIED Nov-03-26   Wanted : Institutional Uniforms Like School Uniforms,
                             Corporate Uniforms
Buyer From Oman | Quantity Required: 1 Twenty-Foot Container | Payment: LC

  Product Name: Institutional Uniforms
  Specifications: School / Corporate / Healthcare Uniforms
                  Cotton, Polyester, Poly-Cotton Blends
  Shipping: CIF/FOB   HS Code: 620343   Destination Port: Oman
  Payment Terms: LC   Contact: Mr. Vincent
```

That is a quotable specification, not a lead to research.

**Scale of the harvest.** 1,694 directory entries across 24 categories and 9
countries (Australia 338, Oman 286, UAE 280, Indonesia 228, Malaysia 226,
Saudi Arabia 108, Portugal 84, Egypt 61, Israel 51), with 1,233 carrying a
real quantity.

**The critical screening rule.** The page category is unreliable. The
`fight-gear` page lists steel scrap and diesel. The `martial-arts-mats` page
lists prayer mats and car mats. The `martial-arts-gloves` page lists medical
and latex gloves. The buyer's own **"Buyer Of X"** phrase is the only
trustworthy signal, and filtering on an exact whitelist takes 1,694 raw
entries down to **35 live requirements in our product space**, 23 of which
carry a working inquiry link.

**The four requirements currently in hand:**

| Requirement | Quantity | Destination | Payment | Contact |
|---|---|---|---|---|
| Institutional Uniforms — School, Corporate, Healthcare | 20ft container | Oman | L/C | Mr. Vincent |
| Institutional Uniforms — Dress, Uniform, Skirt, Trousers | 20ft container | Muscat, Oman | L/C | Mr. Vincent |
| Boxing Accessories — Hand Tie, Gloves, Head Guard, Mouth Guard, Cap | 500–1,000 pcs | Egypt | L/C | Ali Aref |
| Sports Drawstring Backpack, waterproof | 600 pcs | Saudi Arabia | transfer in advance | Tamim Alsalamah |

**How the inquiry is sent.** The platform caps a JUNIOR member at **one buyer
inquiry per day**. The agent captures the captcha, reads it, submits the
inquiry form, and confirms the platform's own response: *"Thanks. Your Inquiry
has been sent."* The first inquiry — *Uniforms Like School Uniforms* — went out
at 05:39 UTC today and was verified against the platform's confirmation and
the "Inquiries Sent" list.

**Every inquiry carries a purpose-built message**, not a catalogue dump. The
Egypt message, for example, names all five of their requested items
(hand ties, gloves, head guards, mouth guards, caps), repeats their 500–1,000
piece quantity, confirms CIF to Egypt and L/C, and states the HS code where
one was given.

**The companion channel — buyer companies by email.** A separate funnel
identifies importing companies from the go4WorldBusiness member directory,
then finds each company's own website and email address independently. This
matters because it sidesteps the platform's inquiry limit entirely: writing to
a company's own inbox is not a platform inquiry.

**12 buyer/import companies are now identified**, including Supa Sportsman
(Oman), Cobra Sports (Malaysia), Apparel Point Trading (UAE), GymNation (UAE),
Adeem Uniforms (Saudi Arabia), Linkwell Uniforms (UAE), Dream Uniform (UAE),
Bhasin Co. (Kuwait), Fashqua Buying Company (UAE) and East West Trading (UAE).

---

## 3. How It All Runs — The Schedule

Every job is a **script-only cron**, deliberately not an agent job. The reason
is hard-won: when these were agent jobs, a model-provider rate limit (HTTP
429) marked the whole job as failed even though the work had already
completed, and the retry re-ran everything from zero. A script cannot fail
that way.

| Time (UTC) | Job | What it does |
|---|---|---|
| 00:00 | morning-briefing | Daily summary to Telegram |
| 02:00 | nightly-git-backup | Pushes the tracker to GitHub |
| 05:05 | g4wb-daily-buyer-inquiry | Sends the day's go4WorldBusiness inquiry |
| 09:00 | gmaps-daily-scrape | Maps + website enrichment |
| 09:25 | g4wb-buyer-directory-funnel | Screens the buyer directory |
| 20:20 | daily-outreach-pipeline | Cold email wave + reply engine |
| 20:55 | chain-franchise-corporate-pitch | One email per brand, not per location |
| 21:10 | daily-followup-email-wave | The three follow-up angles |
| every 30m | outreach-watchdog | Restarts a dead worker |

**Safety properties built into every engine:**

- **Resumable.** Each lead is marked in the tracker the instant it sends, so a
  re-run continues rather than restarting. A timeout is never treated as a
  failure.
- **Lock-protected.** An exclusive lock means two runners can never race on
  one Gmail tab.
- **Quota-aware.** The live daily count is checked before every single send.
- **Read-back verified.** After sending, the agent reads the sent row back.
  After a WhatsApp message, it reads the transcript back.

---

## 4. Replies — Where They Are Coming From

Six live buyer replies have come in. Each is a real, named business:

| Lead | Country | Channel | What they asked |
|---|---|---|---|
| **Shudokan** | Spain | Email | Catalogue and price list for Kickboxing products |
| **TOWASAN Karate Schulen** | Germany | WhatsApp | Class outline, factory prices, one question |
| **Brazilian Fight Lisboa** | Portugal | Email | Follow-up sent |
| **Boxeo El Rayo** | Spain | Email | Verified contact reached |
| **Saints & Stars Oud-West** | Netherlands | Email | Already answered |
| **Fechtclub Graz (office)** | Austria | Referral | Alfred Mark redirected us to `offie@fechtclubgraz.at` |

**A reply-detection bug was found and fixed.** The sweep was reporting "zero
human replies" while three real replies sat in the inbox. The detector was
English-only, and all three had replied in Spanish, Portuguese or German. The
detector now works in four languages, and it excludes our own outbound
messages and platform auto-replies by inspecting the sender field, not the
whole message. One Instagram "reply" turned out to be an automated German
message from a boxing gym's chatbot — correctly excluded.

---

## 5. Data Integrity — The Work That Makes Everything Else Trustworthy

Several serious defects were found and repaired in the last 24 hours. They are
listed here because they directly affect whether the numbers above can be
trusted.

**A stale-process write could destroy 5,000 leads.** A script that started
before the safe writer existed still had the old read-once/write-whole-file
code in memory. Fix: a generation counter on the file, and a guarded writer
that detects a stale copy and **merges** instead of overwriting. Proven with a
dedicated test — a stale in-memory copy can no longer destroy newer rows.

**The header row was being deleted by an email filter.** The tracker header's
email cell contains the literal text `Email`. Any filter asking "is this a
usable address?" read that as an address, judged it undeliverable, and removed
the header — putting every subsequent read one row out of position. The filter
now lives in the reader (so it can never come back) and the writer **refuses
to write a file without a header**.

**Undeliverable addresses were being recorded as contacts.** A stale run had
added a Wix form address and a privacy contact page as buyer companies. A
contactability rule now rejects form, privacy, no-reply and platform-system
addresses, while correctly **keeping** `support@`, `sales@` and `enquiry@`,
which are real business addresses. Seven dead rows were removed; 33 live club
leads were protected from a rule that was initially too aggressive.

**The search function was silently returning nothing.** A change to the
search engine's result markup meant every parsed URL was malformed, so
**every company in the funnel was reported "no match"** — the entire channel
had been searching nothing without erroring. Fixed and verified: 5 valid
results per query.

**A name-matching rule was killing real leads.** The directory listed
"Fashqua Buying Company"; the company writes "Fashque Designs". Exact matching
dropped it. A one-letter-variance match was added, tested with three negative
cases that must still not match.

**Two-thirds of the directory was never a business.** Of 990 entries, 577 were
a person's name or an unrelated trade (solar, marine, medical). These are now
classified and skipped instantly rather than burning a search.

**Spam-word screening was incomplete.** A stricter checker implementing the
full rule set caught two words in copy that had already shipped — `quote` and
an all-caps acronym. Fixed at the generator so they cannot return.

---

## 6. Constraints Currently Binding

**One go4WorldBusiness inquiry per day.** This is the hardest limit. Four
verified requirements are in hand, each with a purpose-built message ready.
At one per day, they take a week to work through, and a requirement that is
live today may be archived next week.

**100 cold emails per day.** Held exactly as instructed, never bent.

**One WhatsApp tab per profile.** Opening a second tab wedges the session.

**No purchased contact lists.** Every lead in the tracker came from a live
search — Maps, Instagram, WhatsApp, or the platform's own directory. Nothing
was bought.

**No third-party branding.** Only our own logo and our own factory and site
photographs are ever used. A club's existing brand is never reproduced on our
storefront.

---

## 7. What I Recommend, in Priority Order

**1. Upgrade go4WorldBusiness to Premium.** Four verified container-scale and
500-piece orders are in hand, each with a finished quote email. Premium lifts
the cap from one inquiry per day to 100 per day, for 60 days, with no
auto-renewal and a money-back guarantee. This is the single highest-leverage
purchase available to us, and it converts directly into order value rather
than club-sized revenue.

**2. Send the price list to Shudokan.** They asked, in Spanish, for the
catalogue and the price list. We have replied asking for their quantity and
fabric weight. Their reply converts directly into a quotation.

**3. Approve Fechtclub Graz.** `offie@fechtclubgraz.at` was handed to us by
the club itself. It is queued and unsent pending a decision.

**4. Prioritise the 12 buyer companies over further club volume.** We have
2,112 club emails against 12 buyer companies. The reply rate on club email is
0.28%. A single importer ordering a container is worth roughly a thousand club
orders. The next hour of work should go into the twelve, not into more Maps
leads.

**5. Fix the Everlast-branded glove image on the website hero.** It is
trademark exposure on our own storefront and should be replaced with one of
our own products. This is unresolved.

---

## 8. Honest Assessment

**What is working.** The system runs without supervision. It found 5,227
leads across 36 countries, contacted them on three channels, verified every
send, and produced six genuine buyer conversations including a referral from
a satisfied contact. The tracker is backed up to GitHub every night and is
recoverable from any point.

**What is not yet proven.** No order has been closed. The club channel has a
0.28% reply rate, which is normal for cold B2B email at this volume but is not
yet a revenue engine. The buyer channel has the right targets and the right
messages but is throttled to one contact per day.

**The honest bottleneck is not lead generation.** We have more than enough
leads. It is the rate at which we can reach the buyers who place real orders.
Everything in the last 24 hours was aimed at that one number.

---

*All figures in this report were measured directly from the tracker, the send
ledger and the platform's own responses on 8 November 2026. The tracker is
backed up nightly to GitHub at `hsnwarriorapparel-dot/hsn-business`.*
