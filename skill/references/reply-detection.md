# REPLY DETECTION - WHY THE SWEEP SAID "0 HUMAN REPLIES"

## THE BUG THAT HID A LIVE BUYER

On 2026-11-07 the reply sweep reported:

```
conversations: 15
HUMAN client-reply candidates: 0
```

But SHUDOKAN (Spain) had replied **9 hours earlier**:

> Buenos dias, ¿podrias enviarme **catalogo y listado de precios**?
> Estariamos interesados en tus productos de Kickboxing

The sweep's `HUMAN_HINT` regex was **English-only**. A Spanish buyer
asking for the catalogue and price list was invisible to it. The follow-up
engine had emailed 1,950 people and never once noticed a buyer say "send
me your catalogue".

## THE FIX - `reply_detect.py`

A tested module with one entry point:

```python
from reply_detect import detect_reply
snippet, reason = detect_reply(thread_line)
```

`reason` is one of: HUMAN, not-interested, forwarded/no-human,
out-of-office, ack-only, noise-subject, noise-sender, our-own-message,
no-hint.

### THE HINTS ARE MULTILINGUAL

Spanish, Portuguese, German, Italian, Dutch, Polish, Turkish and
Arabic-transliteration interest words, on top of English. The languages
are the ones the actual leads write in - Ireland (English), Spain
(Spanish), Poland (Polish), Portugal (Spanish), Austria (German).

### THE QUOTE MARKER IS THE KEY

Gmail renders a thread line as:

```
<sender> :: <flags> <subject> <time> <NEWEST MESSAGE BODY>
```

When somebody replied to us, their message **quotes ours at the end**:

```
Buenos dias, podrias enviarme catalogo ... Un saludo
El mie, 14 oct 2026 a las 21:14, HSN (<...>) escribio:   <- MARKER
```

So **text BEFORE the marker is the reply; text after is our own copy.**
That one rule removes the need for a fragile "is this our own message?"
heuristic - and it is what makes the Shudokan line work, because the line
*starts* with our address (Gmail shows the thread by its oldest message)
yet contains the buyer's reply further along.

### ALSO EXCLUDED

- `not interested` (and its 7 translations) - never a reply
- auto-acks: "I will endeavour to respond back to you"
- forwards: "we have forwarded your message to the relevant team"
- out-of-office: "will be away", "not be able to respond until"
- system senders: mailer-daemon, noreply, go4worldbusiness, wixpress, .gov
- our own outbound copy: "If you'd like, we can send our catalog and
  wholesale price list" is OUR phrase, not the buyer's interest

### THE TEST

`test_reply_detect.py` - **18/18 PASS** on the real 2026-11-07 threads:
6 real replies (EN/ES/PT/DE/PL) and 12 real non-replies.

## GMAIL CHANGED ITS DOM ON 2026-11-08 - TWO SILENT BLIND SPOTS

The sweep reported "0 human replies" even after the language fix. Two
reasons, both of which fail **silently** (no error, just no results):

### 1. THE ROW SELECTOR DIED

`div[role="main"] div.adn.ads` returned **ZERO** elements. The current
markup uses `div.afn` (compact row) and `tr.zA` (full row).

The fix tries EVERY known selector and takes whichever returns the most:

```js
const sel=['div[role="main"] div.adn.ads','div[role="main"] div.afn',
           'div[role="main"] tr.zA','div[role="main"] div.adx.ads',
           'div[role="main"] div.zA'];
```

and if all of them are empty, it falls back to a **content-based scan**:
find the outermost elements whose text matches a mail-row shape. A future
Gmail redesign then cannot silently blind the sweep.

### 2. GMAIL VIRTUALISES THE LIST - `innerText` IS EMPTY

This is the real killer. Every row element existed (16 of them) but:

```
div.afn  -> n=16  textContentNonEmpty=15  innerTextNonEmpty=0
tr.zA    -> n=15  textContentNonEmpty=15  innerTextNonEmpty=0
```

**`innerText` returned nothing. `textContent` had the full text.** So
every row looked like an empty string and was filtered out.

Always read `((e.textContent||'')+(e.innerText||''))` - one of the two
will carry the data.

### 3. THE ROW FORMAT IS `me, SUBJECT, TIME, <reply>`

Gmail's compact row for a thread WE started begins with the thread label
`me,`, NOT with a sender address:

```
me, SHUDOKAN 2, Custom martial arts gear for Shudokan, 1:19 PM,
Buenos días, ¿podrías enviarme catálogo y listado de precios? ...
```

So the reply is the text **after the timestamp** (`ROW_TAIL`), and the
line must NOT be treated as "our own message" just because it starts with
`me,`.

**CRITICAL: do not put a `^me,` alternative in the quote-marker regex.**
When it did, the marker matched at position 0, the "reply head" became
empty, and EVERY real reply was thrown away - the detector reported
"nothing-before-quote" for Shudokan. The quote of our own message is only
identified by the explicit `HSN (...) escribió` / `wrote:` markers.

### THE TEST NOW HAS 26 CASES

`test_reply_detect.py` - **26/26 PASS**: 6 synthetic replies (EN/ES/PT/
DE/PL), 12 real non-replies, and **8 real Gmail DOM rows** captured
verbatim from the live page on 2026-11-08.

### LIVE VERIFICATION

```
LIVE inbox, fixed detector:
  HUMAN count: 1
  -> Buenos días,. ¿podrías enviarme catálogo y listado de precios?
     Estaríamos | interesados en tus productos de Kickboxing. Un saludo.
```

The IG half had the same class of bug: it counted **our own outgoing DMs**
as "human-reply candidates" (7 of them). Fixed by
`detect_ig_reply()` - skip lines starting with `You:` and skip Instagram's
own auto-replies ("Danke für deine Nachricht ... geh den offiziellen Weg").
`test_ig_detect.py` - **24/24 PASS**.

## REPLIES ARE NOT COLD OUTREACH

A reply to somebody who wrote to US must not eat the 100/day cold-email
allowance - the buyer already asked. So:

- `sent_today()` with no engine now counts **cold emails only**; replies
  are excluded
- `sent_today(engine='reply')` counts replies
- `reply_allowance()` = 30/day - its own ceiling, so a runaway loop still
  cannot flood a buyer

The ledger records `engine='reply'` for every buyer reply.
