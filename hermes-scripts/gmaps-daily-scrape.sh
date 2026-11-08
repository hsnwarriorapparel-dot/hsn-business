#!/bin/bash
# Daily 2PM PKT Google Maps + website lead scrape for HSN Warrior Apparels.
#
# WHY THIS IS A SCRIPT-ONLY CRON JOB (2026-11-04): this job used to be an
# agent job (model calls + tool calls). The agent's own NVIDIA call would
# fail with HTTP 429 when the account was busy, which marked the whole job
# as FAILED even though the scrape itself had already completed - and the
# retry re-ran everything from zero. This script does the SAME work with NO
# model calls at all, so it can never hit a provider rate limit.
#
# The scrape is idempotent: it dedupes against leads.csv by email AND phone,
# and it appends only new leads. Re-running is safe.
set -u

PY="$(ls -d /home/ubuntu/.hermes/tools/python-3*/bin/python3 2>/dev/null | head -1)"
[ -z "$PY" ] && PY="/usr/bin/python3"

cd /home/ubuntu || exit 1

# Ensure the scrape engine is up (it serves the Maps API on localhost:8080).
if ! curl -s -m 5 http://localhost:8080/ >/dev/null 2>&1; then
    echo "[gmaps-cron] engine down, starting docker compose..."
    ( cd /home/ubuntu/skill-installs/google-maps-scraper-kit \
      && sudo docker compose up -d ) >> /home/ubuntu/gmaps_scrape_log.txt 2>&1
    # Give the engine a moment to bind its port; the script also waits for it.
    for _ in $(seq 1 30); do
        curl -s -m 3 http://localhost:8080/ >/dev/null 2>&1 && break
        sleep 2
    done
fi

"$PY" /home/ubuntu/gmaps_daily_scrape.py >> /home/ubuntu/gmaps_scrape_log.txt 2>&1
RC=$?

# Report the real numbers straight from the script's own log + leads.csv.
TODAY="$(date -u +%Y-%m-%d)"
NEW=$(grep -c "gmaps 2PM $TODAY" /home/ubuntu/leads.csv 2>/dev/null || echo 0)
echo "gmaps 2PM scrape $TODAY rc=$RC | new leads in leads.csv: $NEW"
echo "--- last lines of gmaps_scrape_log.txt ---"
tail -n 12 /home/ubuntu/gmaps_scrape_log.txt
exit $RC
