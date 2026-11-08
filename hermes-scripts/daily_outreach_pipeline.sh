#!/bin/bash
# Daily outreach pipeline runner (cron: 0 20 * * * = 1:00 AM PKT).
#
# This is a SCRIPT-ONLY cron job (no_agent). That matters: the previous
# version was an agent job, so the whole pipeline depended on a model call
# succeeding. When the model route died (HTTP 404 "Function not found" from
# agentrouter.org, then a dead NVIDIA fallback) the cron failed BEFORE running
# a single email - the day's outreach was simply skipped. A script-only job
# cannot fail that way.
#
# The launcher (/home/ubuntu/run_today_outreach.py) is:
#   - resumable   (each lead is marked 'email sent' in leads.csv the moment
#                  it succeeds, so a re-run continues instead of restarting)
#   - lock-protected (exclusive lock, so a retry never races the original)
#   - quota-aware  (the wave runner enforces the 100/day email cap)
#
# If the launcher exits non-zero or times out, wait 10 minutes and run it
# again - up to 4 times. It resumes; it never double-sends.
set -u
PY=$(ls -d /home/ubuntu/.hermes/tools/python-3*/bin/python3 2>/dev/null | sort -V | tail -1)
if [ -z "$PY" ]; then echo "interpreter not found"; exit 1; fi
LOG=/home/ubuntu/outreach_pipeline.log

echo "=== daily outreach pipeline $(date -u '+%Y-%m-%d %H:%M:%S UTC') ==="

# Make sure TODAY's quota state exists BEFORE anything reads it. Every engine
# takes the campaign day from the newest dayNN_quota_state.json, so without
# this the day never rolls over and the 100/day cap stays spent forever
# (found 2026-11-07 - nothing was creating the new day's file).
"$PY" /home/ubuntu/ensure_quota_state.py 2>&1 | tee -a "$LOG"

for attempt in 1 2 3 4; do
  echo "--- launcher attempt $attempt ---"
  "$PY" /home/ubuntu/run_today_outreach.py 2>&1 | tee -a "$LOG"
  rc=${PIPESTATUS[0]}
  if [ "$rc" -eq 0 ]; then
    echo "launcher finished cleanly (rc=0)"
    break
  fi
  echo "launcher exited rc=$rc - resuming in 10 minutes (it resumes, never double-sends)"
  if [ "$attempt" -lt 4 ]; then sleep 600; fi
done

echo "--- final counters ---"
"$PY" /home/ubuntu/hsn_counters.py 2>&1 | tail -14

# the reply engine: catch buyers who wrote to us and answer them.
# It is separate from the cold engines - a reply is not cold outreach
# and must not eat the 100/day cold allowance.
"$PY" /home/ubuntu/reply_engine.py 2>&1 | tee -a "$LOG"

# The REPLY SWEEP does three things the reply engine does not:
#   1. scans 30 days for STOP / opt-out phrases and marks them, so we
#      never contact a lead who asked us to stop
#   2. marks 2-day email bounces as failed, so a dead mailbox is never
#      sent to again
#   3. sweeps the Instagram inbox for replies, in any language
#
# It was only ever run by hand. A buyer who wrote to us overnight, or
# whose message bounced, should not wait until someone noticed.
# It is read-only apart from the marker it writes, and it runs AFTER
# the reply engine so a reply is handled before anything else.
"$PY" /home/ubuntu/day24_reply_sweep.py 2>&1 | tee -a "$LOG"

exit 0
