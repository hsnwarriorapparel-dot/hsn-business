#!/bin/bash
# Stage 4: Post pipeline - IG hunt + tracker rebuild + backup (runs 0 3 * * * = 8:00 AM PKT)
# Completes in ~10-20 min
set -u
PY=$(ls -d /home/ubuntu/.hermes/tools/python-3*/bin/python3 2>/dev/null | sort -V | tail -1)
if [ -z "$PY" ]; then echo "interpreter not found"; exit 1; fi
LOG=/home/ubuntu/outreach_pipeline.log

echo "=== daily outreach pipeline STAGE 4 - POST PIPELINE $(date -u '+%Y-%m-%d %H:%M:%S UTC') ===" | tee -a "$LOG"

timeout 1800 "$PY" /home/ubuntu/day24_post_pipeline.py 2>&1 | tee -a "$LOG"

echo "=== STAGE 4 COMPLETE ===" | tee -a "$LOG"
exit 0
