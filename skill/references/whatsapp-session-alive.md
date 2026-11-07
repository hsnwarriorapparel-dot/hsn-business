# WhatsApp was NEVER dead — the "QR-dead" reports were stale (verified 2026-11-07)

## The finding

For ~2 weeks every report said "WhatsApp is QR-dead, the user must re-link".
That was WRONG. On 2026-11-07 the WA tab was checked properly and the session
was **fully alive**: 20 chat rows, a real chat pane, and our own outreach
messages sitting in the inbox.

## How to check the truth

```bash
python3 /home/ubuntu/wa_deep_check.py
```

Interpretation:
- `#pane-side` present + **no** `canvas` + **no** "Scan to log in" in the body
  -> **SESSION IS LIVE**. The 10/day WA quota is usable.
- "Scan to log in" in the body -> genuinely logged out; only then capture a QR.

**Never declare WA dead from a stale QR file or an old report.** The
`capture_wa_qr.py` script prints `NO_QR_ELEMENT - page may not be the login
screen` when the page is actually the chat list - that message is the SUCCESS
case, not a failure.

## Reading a chat

```bash
python3 /home/ubuntu/wa_read_chat.py <NAME>
```

Two gotchas that cost real time:
- `div[role="listitem"]` and `document.querySelector('div[role="main"]')` go
  STALE after you click a chat - they return nothing. Use
  `span[title]` attributes instead; WhatsApp puts the chat name AND the last
  message preview there.
- The chat list is a `[role="grid"]`; the OPEN conversation is a second grid.
  Dump every grid and pick the one that is not the list.

## The reply we found

**TOWASAN Karate Schulen (L3372, Germany)** replied on WhatsApp:

> "What kind of class are you proposing, and what would your role be? Please
> share a short outline so our team can review it."

This is a HUMAN reply to our IG DM. It was sitting in the WA inbox the whole
time while the reports said the session was dead. It is recorded in
leads.csv as `WA REPLY (2026-11-07)` and is **DRAFT-ONLY** - the user has not
approved a reply.

Second WA contact visible: **Gauntlet Fight Academy (L3493, UK)** - received
our outreach message, no reply yet.

## Why this matters

The 10/day WA quota was frozen for 2 weeks on a false premise. Every report
told the user to scan a QR that was not needed. Always verify session state
with a live DOM probe before asking the user to do anything.
