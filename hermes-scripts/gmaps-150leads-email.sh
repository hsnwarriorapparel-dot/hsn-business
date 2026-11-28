#!/bin/bash
# Google Maps 150-lead scrape + email outreach
# Runs at 05:00 UTC (10:00 PKT) - dedicated slot with no other cron jobs
# Scrapes 6 cities (3x normal) to target ~150 leads, then feeds outreach pipeline

set -u

PY="$(ls -d /home/ubuntu/.hermes/tools/python-3*/bin/python3 2>/dev/null | head -1)"
[ -z "$PY" ] && PY="/usr/bin/python3"

cd /home/ubuntu || exit 1

DATE=$(date -u +%Y-%m-%d)
LOG="/home/ubuntu/gmaps_150leads_log.txt"

log() {
    line="$(date -u +%H:%M:%S) $*"
    echo "$line" | tee -a "$LOG"
}

# Ensure Maps engine is up
if ! curl -s -m 5 http://localhost:8080/ >/dev/null 2>&1; then
    log "engine down, starting docker compose..."
    (cd /home/ubuntu/skill-installs/google-maps-scraper-kit && sudo docker compose up -d) >> "$LOG" 2>&1
    for _ in $(seq 1 30); do
        curl -s -m 3 http://localhost:8080/ >/dev/null 2>&1 && break
        sleep 2
    done
fi

# Run expanded scrape (6 cities instead of 2)
"$PY" /home/ubuntu/gmaps_150leads_scrape.py >> "$LOG" 2>&1
RC=$?

# Report results
NEW=$(grep -c "gmaps 150leads $DATE" /home/ubuntu/leads.csv 2>/dev/null || echo 0)
log "gmaps 150leads scrape $DATE rc=$RC | new leads in leads.csv: $NEW"

# If we got leads, trigger the outreach feed + email wave
if [ "$NEW" -gt 0 ]; then
    log "New leads found ($NEW) - feeding outreach pipeline..."
    
    # Run merge/dedup to qualify new leads
    "$PY" /home/ubuntu/lead_gen_system/scripts/merge_dedup.py \
        --input /home/ubuntu/leads.csv \
        --output /home/ubuntu/lead_gen_system/data/merged_leads.csv >> "$LOG" 2>&1
    
    "$PY" /home/ubuntu/lead_gen_system/scripts/qualify_leads.py \
        --input /home/ubuntu/lead_gen_system/data/merged_leads.csv \
        --output /home/ubuntu/lead_gen_system/data/qualified_leads.csv >> "$LOG" 2>&1
    
    "$PY" /home/ubuntu/lead_gen_system/scripts/verify_websites.py \
        --input /home/ubuntu/lead_gen_system/data/qualified_leads.csv \
        --output /home/ubuntu/lead_gen_system/data/verified_leads.csv >> "$LOG" 2>&1
    
    "$PY" /home/ubuntu/lead_gen_system/scripts/validate_emails.py \
        --input /home/ubuntu/lead_gen_system/data/verified_leads.csv \
        --output /home/ubuntu/lead_gen_system/data/validated_leads.csv >> "$LOG" 2>&1
    
    "$PY" /home/ubuntu/lead_gen_system/scripts/feed_pipeline.py \
        --input /home/ubuntu/lead_gen_system/data/validated_leads.csv \
        --output /home/ubuntu/lead_gen_system/data/outreach_feed.csv \
        --limit 150 >> "$LOG" 2>&1
    
    # Trigger email wave (stage 3 of outreach pipeline)
    log "Triggering email outreach wave..."
    /home/ubuntu/.hermes/scripts/daily_outreach_pipeline_stage3.sh >> "$LOG" 2>&1
    /home/ubuntu/.hermes/scripts/daily_outreach_pipeline_stage3.sh >> "$LOG" 2>&1
    /home/ubuntu/.hermes/scripts/daily_outreach_pipeline_stage3.sh >> "$LOG" 2>&1
    /home/ubuntu/.hermes/scripts/daily_outreach_pipeline_stage3.sh >> "$LOG" 2>&1
    /home/ubuntu/.hermes/scripts/daily_outreach_pipeline_stage3.sh >> "$LOG" 2>&1
    /home/ubuntu/.hermes/scripts/daily_outreach_pipeline_stage3.sh >> "$LOG" 2>&1
    
    log "Email waves complete (6 waves x 25 = ~150 emails)"
fi

log "=== GMAPS 150LEADS + EMAIL COMPLETE ==="
exit $RC