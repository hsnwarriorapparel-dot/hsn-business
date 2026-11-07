# Counters — the "today" block that reported zero

`hsn_counters.py` prints a "today" block (rows touched / emails sent today /
IG done today / WA sent today / countries). It is the canonical source for
every report, so a wrong number here corrupts every briefing.

## The bug (found 2026-11-05)

The day tag was detected as `max()` over EVERY `YYYY-MM-DD` date appearing in
ANY Status marker — including lead-source stamps:

```
HUNTED (gmaps 2PM 2026-11-05)     <- 72 rows, a LEAD-SOURCE stamp
COMPLETE: email sent (Daily 2026-11-04)   <- 99 rows, a real SEND
IG follow=ok dm=sent (Daily 2026-11-04)   <- 188 rows, a real SEND
```

The gmaps scrape stamps the **UTC** date; the outreach wave carries the **PKT
campaign-day** tag. So the scrape date is often a day AHEAD of the sends and
wins `max()`. The counter then reported:

```
--- today 2026-11-05 ---
emails sent today: 0      <- on a day that sent 99 emails and 188 IG DMs
IG done today: 0
```

The morning briefing and the counters both understated the day's work. Two
different scripts disagreed, which is what exposed it: `day21_verify.py`
(counts a fixed day tag) said 99, `hsn_counters.py` said 0.

## The fix

Only markers that record an actual OUTREACH action may define the campaign day.
Lead-source stamps are EXCLUDED:

```python
SOURCE_MARKER_RE = re.compile(r'HUNTED\s*\(')
outreach_markers = ('email sent', 'ig follow', 'dm=sent', 'ig done',
                     'whatsapp sent', 'wa sent', 'email failed', 'replied')
for part in status.split('|'):
    if SOURCE_MARKER_RE.search(part):
        continue
    if not any(k in part.lower() for k in outreach_markers):
        continue
    found.update(re.findall(r'20\d\d-\d\d-\d\d', part))
```

Now:
```
--- today 2026-11-04 ---
rows touched: 288
emails sent today: 99
IG done today: 188
countries: {'USA': 51, 'Ireland': 3, 'Netherlands': 19, 'France': 5, 'Germany': 21}
```

## Also fixed: the detector ran per row

`_detect_today_tag()` was called inside the list comprehension
`[r for r in rows[1:] if _detect_today_tag() in ...]`, so with the new
per-marker scan it re-scanned every Status for all 4019 rows and the script
took **>2 minutes** (it used to be cached and instant). Resolve the tag ONCE:

```python
_tag = _detect_today_tag()
today = [r for r in rows[1:] if _tag and _tag in g(r, 'Status')]
```

Runtime is now **0.13s**.

## Override for a manual re-run

```bash
HSN_TODAY_TAG=2026-11-02 python3 /home/ubuntu/hsn_counters.py
```

## Cross-check against dayNN_verify.py

Two independent implementations exist and should agree:
- `hsn_counters.py` — campaign-wide, auto-detected day
- `dayNN_verify.py` — fixed day tag for that run

A mismatch is a bug in one of them. Note the IG numbers legitimately differ:
`dayNN_verify` counts only follow+DM SUCCESSES (182), the counter counts all
IG touches that day (188, including mismatches and not-found rows). Emails
must match exactly (99).

## Why this matters

The counter feeds the morning briefing, the Telegram reports and the
user-facing "what did you do" answers. Reporting 0 sends on a 99-send day
makes the whole campaign look broken and invites a re-run that double-sends.
