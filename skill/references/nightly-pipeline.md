# The nightly pipeline

## THE REPLY SWEEP WAS NEVER SCHEDULED

`day24_reply_sweep.py` did three things the nightly pipeline did NOT do:

1. scanned 30 days for STOP / opt-out phrases and marked those leads, so
   we never contact someone who asked us to stop
2. marked 2-day email bounces as failed, so a dead mailbox is never sent
   to again
3. swept the Instagram inbox for replies, in any language

It only ever ran when someone remembered to invoke it by hand. A buyer
who wrote to us overnight, or whose message bounced, waited until
somebody noticed.

It now runs in `daily_outreach_pipeline.sh`, AFTER `reply_engine.py`:

```bash
"$PY" /home/ubuntu/reply_engine.py 2>&1 | tee -a "$LOG"
"$PY" /home/ubuntu/day24_reply_sweep.py 2>&1 | tee -a "$LOG"
```

**`reply_engine.py` only DRAFTS unless `--send` is passed.** The nightly
pipeline calls it without that flag on purpose: a reply to a real buyer
gets prepared for review, never sent blind. Keep it that way.

## THE BACKUP REPO WAS MISSING THE AUTOMATION ITSELF

`backup-git.sh` copied `leads.csv`, the tracker, `*.py`, the skill and
the website - but NOT `.hermes/scripts/`. A lost VPS would have kept the
data and the knowledge base while losing everything that RUNS them.

Now it also syncs:

```bash
mkdir -p "$BACKUP_DIR/hermes-scripts"
cp -ru /home/ubuntu/.hermes/scripts/. "$BACKUP_DIR/hermes-scripts/" 2>/dev/null
mkdir -p "$BACKUP_DIR/hermes-cron"
cp -ru /home/ubuntu/.hermes/cron/jobs.json "$BACKUP_DIR/hermes-cron/" 2>/dev/null
```

**Back up only the cron DEFINITIONS.** The `output/` archive, the
`notepad.db`, the tickers and the runtime databases are live state and a
growing archive - copying them made every backup dirty and pushed
hundreds of files. The backup now holds 10 scripts + `jobs.json`, and
the backed-up `jobs.json` must stay byte-identical to the live one.

## THE CAMPAIGN DAY IS NOT THE CALENDAR DATE

`day_tag()` returns the date in the NEWEST `dayNN_quota_state.json`, not
today's date. `ensure_quota_state.py` creates that file at the start of
each pipeline run, so the ledger, the quota and the chain guard all move
to the next campaign day together.

This matters when the pipeline has not run for a while: at 03:20 UTC on
9 November the newest state was still `day25` (date 2026-11-08), so
`sent_today()` reported 100 - the full quota - because the 100 emails
sent after midnight still belonged to the 8 November campaign day.

Running `ensure_quota_state.py` creates `day26_quota_state.json` for
2026-11-09 and the counter correctly resets to 0. The 8 November sends
stay archived under that day in the ledger.

**The chain pitch has its OWN `day_tag()`** that returns
`'Daily 2026-11-09'` (a different format from `outreach_quota`'s
`'2026-11-09'`), because the chain state file stores the tracker-style
day tag. Do not mix the two formats.

**A brand pitched yesterday is available again today.** The chain guard
keys on the campaign day, not on all-time history, so the brands
re-pitch at 20:55 each day. That is deliberate - a franchise pitch
every night to the same corporate inbox would be spam, so check that
the state file's date format matches the engine's `day_tag()` exactly.

## THE PIPELINE FAILED THREE NIGHTS RUNNING AND NOTHING SAID SO

The nightly pipeline was killed by the 1-hour cron timeout inside the IG
pass. The log's last line was an ordinary progress line, so a partial
run looked like a normal run that happened to stop. The tracker rebuild,
the WA list, the reply sweep and the final verify were **never reached**,
three nights in a row, and the cron only reported a generic timeout.

**The cause was a batch size set to exactly double what fits.**

| | |
|---|---|
| measured cost | 37.4 seconds per IG account |
| batch size | 240 accounts |
| time needed | 2.5 hours |
| cron window | 3600 seconds |

The IG pass is RESUMABLE - it skips any handle already touched - so the
remainder is picked up on the next night. Sized to fit:

```python
IG_PASS_BATCH = 70      # 70 x 37.4s = 44 minutes
```

**MEASURE the per-item cost from the logs, never assume it.** The IG log
carries a timestamp on every line:

```python
per = (sec(last) - sec(first)) / (len(lines) - 1)
```

## A SILENT PARTIAL RUN MUST BE IMPOSSIBLE

The post-pipeline now writes `pipeline_completed.json` ONLY when every
step has run. The watchdog reports a stale one.

**Two traps in the watchdog implementation:**

1. the check must come BEFORE any `exit 0` - the worker-restart branch
   exits early when `worker_restart.lock` exists, so a check placed
   after it never ran
2. `python - <<'EOF'` does NOT execute the heredoc here - the
   interpreter reads the script from stdin and the body is consumed
   differently. Write the check to a temp file and run it:

```bash
_wd_check=$(mktemp)
cat > "$_wd_check" <<'PYEOF'
...
PYEOF
"$PY" "$_wd_check"
rm -f "$_wd_check"
```

Test all three cases: a stale marker must be REPORTED, today's marker
must be SILENT, and a missing marker must not crash.
