# Outreach Pipeline Timing — the 4-hour timeout that killed every night

Measured 2026-11-05 on the day21 run. The pipeline needs ~6h25m; the launcher
had a 4h cap, so it was killed during the IG follow+DM pass every single night
and the last stages (git backup, reply sweep, final verify) never ran.

## Measured stage timings

| Stage | Duration |
|---|---|
| site-verify + wave build (100 leads) | 75s |
| email wave — 100 leads @ 38s Gmail-safe pacing | 87 min |
| IG handle hunt (wave, 74 leads) | 50s |
| IG handle hunt (backlog, 1063 rows) | 10 min |
| IG follow+DM pass — 240 candidates @ ~40s | 2h21m |
| tracker rebuild | ~1s |
| WA pending list + git backup + reply sweep + verify | ~2 min |
| **TOTAL** | **~6h25m** |

## The caps that must cover it

- Launcher (`run_today_outreach.py`): `OUTREACH_TIMEOUT_S` default **36000** (10h)
- Per-step inside `dayNN_run.py` and `dayNN_post_pipeline.py`: `timeout=21600` (6h)

The per-step cap matters as much as the outer one: the IG pass alone is 2h21m,
so a 4h per-step cap on a long chain leaves no headroom for a retry.

## Rule: measure, then set the cap

Never guess a timeout. Run the chain once, sum the stages, and set the cap
above that total with margin. A timeout that fires mid-pipeline looks like
"the job died" and — because the launcher is resumable — silently skips
whatever came after it. The morning report then shows a successful-looking run
with missing backup and no reply sweep.

## A killed run is NOT a failed run

The launcher reported `orchestrator TIMEOUT` and exited 124 even though the
email wave had completed with `pending=0`. Check what actually finished before
re-running anything:

```bash
grep 'WAVE COMPLETE' /home/ubuntu/dayNN_log.txt     # email wave result
grep 'IG PASS DONE'  /home/ubuntu/dayNN_ig_log.txt   # IG pass result
grep -E '^---' /home/ubuntu/dayNN_pipeline_log.txt   # which stages ran
ls -la /home/ubuntu/HWA_Lead_Tracker.xlsx            # rebuild timestamp
```

The 2026-11-05 run had finished the email wave (99 sent) AND the IG pass
(182 follow+DM) AND the tracker rebuild before the timeout — only the git
backup, reply sweep and final verify were missing. Re-running the launcher
would have re-entered the whole chain for no reason.

## Always run the backup separately after a kill

The git backup lives at the END of the post-pipeline, so a timeout loses it.
Run it directly — it is idempotent and now reports the real push result:

```bash
bash /home/ubuntu/.hermes/scripts/backup-git.sh
```

Then confirm: `git status -sb` shows no "ahead N", and the remote SHA equals
local HEAD.

## Reply sweep needs the RELIABLE Gmail method

`dayNN_reply_sweep.py` navigates by hash-URL, which the skill already flags as
silently failing (the query never applies; the page keeps showing the old
list). When checking replies, use `gmail_counter.py` — it TYPES into the real
Search-mail input and reads the rendered result. A hash-URL sweep reporting
"0 replies" means nothing; always confirm with the typing method before
telling the user there are no replies.

## Known-good outcome for 2026-11-04 (day21)

- 99 emails sent, 1 failed (compose-focus), 0 skipped
- 182 IG follow+DM, 52 not found, 6 chain-dedup, 0 errors
- 72 new gmaps leads
- 0 human client replies (only auto-acks)
