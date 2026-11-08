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
