#!/bin/bash
# go4WorldBusiness buyer-directory pipeline (cron: 25 9 * * *).
# Batched: only screens 20 companies per run.
# Harvest + company_reach run weekly via separate cron jobs.
set -u
PY=$(ls -d /home/ubuntu/.hermes/tools/python-3*/bin/python3 2>/dev/null | sort -V | tail -1)
if [ -z "$PY" ]; then echo "interpreter not found"; exit 1; fi
LOG=/home/ubuntu/g4wb_dir_pipeline_log.txt

echo "=== g4wb buyer-directory pipeline $(date -u '+%Y-%m-%d %H:%M:%S UTC') ==="

# Skip harvest - run separately via weekly cron
# "$PY" /home/ubuntu/g4wb_dir_harvest.py --pages 4 2>&1 | tee -a "$LOG"
# "$PY" /home/ubuntu/g4wb_filter_harvest.py 2>&1 | tee -a "$LOG"
# "$PY" /home/ubuntu/g4wb_company_harvest.py --pages 1 2>&1 | tee -a "$LOG"

# 4a: SCREEN against each buyer's own go4WorldBusiness profile.
# Process in small batches (--limit 20) to stay within cron timeout.
"$PY" /home/ubuntu/screen_buyers.py --limit 20 2>&1 | tee -a "$LOG"

# 4b: REACH - find company websites and emails (web search per company)
# Browser-based search too slow for daily cron; run weekly instead
# "$PY" /home/ubuntu/company_reach.py --limit 2 2>&1 | tee -a "$LOG"

# report
"$PY" /home/ubuntu/g4wb_pipeline_report.py 2>&1 | tee -a "$LOG"
exit 0
