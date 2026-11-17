#!/bin/bash
# Stage 3: Email wave batch (runs every 30 min: 0,30 21-23 * * * = 2:00 AM - 4:30 AM PKT)
# Sends 25 emails per run at 38s pace = ~16 min + overhead = ~20 min
# Run 4 times to complete 100 emails
set -u
PY=$(ls -d /home/ubuntu/.hermes/tools/python-3*/bin/python3 2>/dev/null | sort -V | tail -1)
if [ -z "$PY" ]; then echo "interpreter not found"; exit 1; fi
LOG=/home/ubuntu/outreach_pipeline.log

echo "=== daily outreach pipeline STAGE 3 - EMAIL WAVE BATCH $(date -u '+%Y-%m-%d %H:%M:%S UTC') ===" | tee -a "$LOG"

# Send up to 25 emails per batch
timeout 1200 "$PY" /home/ubuntu/day24_wave_runner.py --limit 25 2>&1 | tee -a "$LOG"

echo "=== STAGE 3 COMPLETE ===" | tee -a "$LOG"
exit 0
