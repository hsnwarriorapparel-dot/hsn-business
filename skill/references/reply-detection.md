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

## REPLIES ARE NOT COLD OUTREACH

A reply to somebody who wrote to US must not eat the 100/day cold-email
allowance - the buyer already asked. So:

- `sent_today()` with no engine now counts **cold emails only**; replies
  are excluded
- `sent_today(engine='reply')` counts replies
- `reply_allowance()` = 30/day - its own ceiling, so a runaway loop still
  cannot flood a buyer

The ledger records `engine='reply'` for every buyer reply.
