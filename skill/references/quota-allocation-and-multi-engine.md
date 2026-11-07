# Quota allocation + multi-engine accounting (2026-11-07)

Three engines send cold email through ONE Gmail tab:
- `dayNN_wave_runner.py`     - first-touch wave   (cron 20:00)
- `dayNN_chain_pitch.py`     - corporate pitches  (cron 20:55)
- `dayNN_followup.py`        - follow-ups         (cron 21:10)

## THE FIVE BUGS THIS FIXED

1. **COUNTING ROWS, NOT EMAILS.** `chain_pitch.mark_sent()` stamps
   `chain pitch sent` on EVERY tracked location of the brand. Brooklyn
   Fitboxing = 21 rows for ONE email. Counting CSV rows inflated the day's
   total up to 13x, so the quota could look full when nothing went out.
2. **EACH ENGINE IGNORED THE OTHERS.** The wave counted only `email sent`,
   the follow-up only `email sent` + `follow-up sent`, the chain pitch
   NOTHING. Three engines, three numbers, one 100/day cap.
3. **THE WAVE TOOK THE WHOLE ALLOWANCE.** The wave was allowed to send all
   100, so the chain pitch (20:25) and the follow-up engine (20:40) both saw
   100/100 and ALWAYS deferred. The follow-up engine - 938 eligible leads,
   the only thing that earns a reply - had never run once.
4. **TWO ENGINES SENDING AT ONCE.** The wave sends 72 emails at ~38s pacing
   = ~46 minutes, so it was still running at 20:25 when the chain pitch
   fired. Both drive the SAME Gmail tab by clicking Compose, so they
   corrupt each other's drafts.
5. **STALE DAY NUMBERS IN THE WRAPPERS.** `followup_daily.sh` called
   `day23_followup.py` and `chain_pitch_daily.sh` called
   `day23_chain_pitch.py` - hardcoded, so they ran yesterday's engine with
   yesterday's accounting. Both now auto-detect the newest
   `day*_followup.py` / `day*_chain_pitch.py`, like `wave_guard.sh` does.

## THE FIX: ONE LEDGER, ONE ALLOCATION, ONE LOCK

**`/home/ubuntu/outreach_quota.py`** - shared by all three engines.

### The ledger
`/home/ubuntu/send_ledger.jsonl` - one JSON line per ACTUAL email sent:
```json
{"day":"2026-11-07","engine":"wave","target":"L1234","note":"...","ts":"..."}
```
Counting EMAILS, not rows. `record_send(engine, target, note)` is called
ONLY after `gmail_send()` returned ok. The CSV Status markers stay for
per-lead resumability but are never used for counting.
`seed_ledger_from_csv()` writes `legacy-csv` entries once so a restart
cannot reset the cap.

### The allocation - read from dayNN_quota_state.json
```
daily_email_quota = 100    (hard cap, unchanged)
followup_reserve  =  20
chain_reserve     =   8
wave allowance    = 100 - 20 - 8 = 72
```
`wave_allowance()` = `min(wave_cap - wave_used, daily - sent_today())`
`chain_allowance()` = `min(chain_reserve - chain_used, daily - sent_today())`
`followup_allowance()` = `daily - sent_today() - chain_left`

### THE FOLLOW-UP ALLOWANCE BUG (found 2026-11-07 21:45)

The follow-up engine runs LAST (21:10), so its allowance was written as
`daily - sent_today()` - "take whatever is left". But that left NOTHING for
the chain pitches: the follow-up engine ate the chain's reserved slice and
the chain pitches (20:55) would have found `chain_allowance() == 0` and
skipped every brand.

The follow-up engine actually ran at 21:10 with 72 already sent, so it
started sending and the day's total climbed 72 -> 85. Fixed:

```python
chain_left = max(0, a['chain_reserve'] - sent_today(engine='chain'))
return max(0, a['daily'] - used - chain_left)
```

Now at 85 sent: follow-up 7, chain 8, total exactly 15. Both engines are
protected no matter which one runs first.

**ALWAYS give every engine an allowance that subtracts the OTHER engines'
unused reserves.** A "take what's left" rule hands the whole cap to
whoever runs last.

### The Gmail send lock
`/home/ubuntu/gmail_send.lock` - exclusive create, holds pid + engine name.
`claim_slot(engine, wait_s, log)` / `release()`. A stale lock (owner pid
gone) is reclaimed automatically. The wave holds the tab for its whole run;
the chain pitch waits up to 60s; the follow-up waits up to 90s then defers
to the next tick.

## PROOF

`sim_quota.py` simulates all 6 orderings of the three engines with the
ledger and the lock. Result: **exactly 100 in every ordering, never 101.**
The split when every engine wants more than its share:
wave 72 · chain 8 · followup 20 = 100.

## TIMING (why the crons are at 20:00 / 20:55 / 21:10)

| Engine | When | How long | Emails |
|---|---|---|---|
| wave | 20:00 | ~46 min (72 @ 38s) | 72 |
| chain pitch | 20:55 | ~6 min (8 @ 40s) | 8 |
| follow-up | 21:10 | ~14 min (20 @ 40s) | 20 |

The old 20:25 / 20:40 slots collided with the still-running wave.

## GOTCHAS

- `emails_sent_today.py` counts CSV ROWS - do not use it for quota. Use
  `outreach_quota.sent_today()`.
- The wave file is BUILT by `dayNN_build_wave.py`; there is no
  `day24_wave.txt` until it runs. Missing wave file is not an error.
- The wave builder excludes junk names, unverified emails and already-sent
  leads. A 100-lead wave from fresh ammo looks like Poland 48, Austria 17,
  Denmark 14 - that is correct, it is the newest ammo first.
- Hard bounces must be suppressed: mark the row
  `BOUNCED (hard bounce <date> - suppressed, do not re-contact)`.
  3 were suppressed on 2026-11-07 (xindojo@protonmail.com,
  webmaster@portlandjujitsu.com, info@playjitsu-academy.com).
- A Gmail tab left on a `?compose=<id>` URL breaks sending. Keep exactly
  ONE clean Gmail tab. `outreach.gmail_send` picks a clean one and
  navigates a dirty one back to the inbox.
- Close scratch browser tabs when done - the work browser had 112
  go4WorldBusiness tabs open, which slows every `get_tabs()` call.
