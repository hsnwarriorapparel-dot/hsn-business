#!/bin/bash
# Follow-up email runner (cron: 40 20 * * *).
#
# Runs AFTER the first-touch wave (0 20 * * *) and AFTER the chain pitches
# (25 20 * * *). The day's cold-email quota is checked live before every
# send, so the follow-ups never push us over the user's hard 100/day limit.
#
# WHY: 1,950 first-touch emails had produced only 6 follow-ups, and the B2B
# playbook says buyers need 5-7 touches. 889 leads are follow-up eligible
# (emailed 5+ days ago, no reply, no decline, no STOP).
set -u
PY=$(ls -d /home/ubuntu/.hermes/tools/python-3*/bin/python3 2>/dev/null | sort -V | tail -1)
if [ -z "$PY" ]; then echo "interpreter not found"; exit 1; fi
LOG=/home/ubuntu/day23_followup_log.txt

echo "=== follow-up run $(date -u '+%Y-%m-%d %H:%M:%S UTC') ==="

# The engine reads the shared ledger (send_ledger.jsonl) for the daily count,
# so it can never exceed the 100/day cap no matter which engine ran first.
# Auto-detect the newest dayNN engine so this wrapper never goes stale when
# tomorrow's day25 files appear.
ENGINE="$(ls -1t /home/ubuntu/day*_followup.py 2>/dev/null | head -1)"
if [ -z "$ENGINE" ]; then echo "no follow-up engine found"; exit 1; fi
echo "engine: $ENGINE"

"$PY" "$ENGINE" 2>&1 | tee -a "$LOG"
exit 0
