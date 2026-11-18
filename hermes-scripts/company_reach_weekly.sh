#!/bin/bash
# Weekly company_reach - find company websites and emails (cron: 0 4 * * 0).
# Browser-based search, runs Sunday 04:00 UTC. Processes ~20 companies.
set -u
PY=$(ls -d /home/ubuntu/.hermes/tools/python-3*/bin/python3 2>/dev/null | sort -V | tail -1)
if [ -z "$PY" ]; then echo "interpreter not found"; exit 1; fi
LOG=/home/ubuntu/company_reach_weekly_log.txt

echo "=== company_reach weekly $(date -u '+%Y-%m-%d %H:%M:%S UTC') ===" | tee -a "$LOG"

# Process 20 companies per weekly run
"$PY" /home/ubuntu/company_reach.py --limit 20 2>&1 | tee -a "$LOG"

echo "=== company_reach complete $(date -u '+%Y-%m-%d %H:%M:%S UTC') ===" | tee -a "$LOG"
exit 0