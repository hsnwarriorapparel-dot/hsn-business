#!/bin/bash
# Weekly harvest of go4WorldBusiness buyer companies (cron: 0 2 * * 0).
# Fetches 1 page per country/category to keep runtime reasonable (~30 min).
set -u
PY=$(ls -d /home/ubuntu/.hermes/tools/python-3*/bin/python3 2>/dev/null | sort -V | tail -1)
if [ -z "$PY" ]; then echo "interpreter not found"; exit 1; fi
LOG=/home/ubuntu/g4wb_weekly_harvest_log.txt

echo "=== g4wb weekly harvest $(date -u '+%Y-%m-%d %H:%M:%S UTC') ===" | tee -a "$LOG"

"$PY" /home/ubuntu/g4wb_dir_harvest.py --pages 1 2>&1 | tee -a "$LOG"
"$PY" /home/ubuntu/g4wb_filter_harvest.py 2>&1 | tee -a "$LOG"
"$PY" /home/ubuntu/g4wb_company_harvest.py --pages 1 2>&1 | tee -a "$LOG"

echo "=== harvest complete $(date -u '+%Y-%m-%d %H:%M:%S UTC') ===" | tee -a "$LOG"
exit 0