#!/bin/bash
# Fast followup engine - runs every 2 hours during business hours
# PACE = 20s, batch size = 15 (15 * 20s = 300s = 5 min + overhead = ~10 min)
set -u
PY=$(ls -d /home/ubuntu/.hermes/tools/python-3*/bin/python3 2>/dev/null | sort -V | tail -1)
if [ -z "$PY" ]; then echo "interpreter not found"; exit 1; fi
LOG=/home/ubuntu/followup_fast.log

echo "=== FAST FOLLOWUP ENGINE $(date -u '+%Y-%m-%d %H:%M:%S UTC') ===" | tee -a "$LOG"

timeout 600 "$PY" /home/ubuntu/day24_followup_fast.py --limit 15 2>&1 | tee -a "$LOG"

echo "=== FAST FOLLOWUP COMPLETE ===" | tee -a "$LOG"
exit 0
