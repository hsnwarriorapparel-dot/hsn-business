#!/bin/bash
# Stage 2: Site verify + build wave (runs 30 20 * * * = 1:30 AM PKT)
# Completes in ~5-10 min.
set -u
PY=$(ls -d /home/ubuntu/.hermes/tools/python-3*/bin/python3 2>/dev/null | sort -V | tail -1)
if [ -z "$PY" ]; then echo "interpreter not found"; exit 1; fi
LOG=/home/ubuntu/outreach_pipeline.log

echo "=== daily outreach pipeline STAGE 2 - SITE VERIFY + BUILD WAVE $(date -u '+%Y-%m-%d %H:%M:%S UTC') ===" | tee -a "$LOG"

timeout 600 "$PY" /home/ubuntu/day24_site_verify.py 2>&1 | tee -a "$LOG"
timeout 600 "$PY" /home/ubuntu/day24_build_wave.py 2>&1 | tee -a "$LOG"

echo "=== STAGE 2 COMPLETE ===" | tee -a "$LOG"
exit 0
