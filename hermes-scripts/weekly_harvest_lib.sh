#!/usr/bin/env bash
# Library of functions for weekly deep harvest

CONFIG="/home/ubuntu/lead_gen_system/icp_config.yaml"
SCRIPT_DIR="/home/ubuntu/lead_gen_system/scripts"
LOG_DIR="/home/ubuntu/lead_gen_system/logs"
STATE_DIR="/home/ubuntu/lead_gen_system/state"

log() {
    echo "[$(date -u +"%Y-%m-%d %H:%M:%S UTC")] $*"
}

# Load qualified companies from master leads for lookalike expansion
get_seed_companies() {
    local date_stamp=$1
    /usr/bin/python3 -c "
import csv
with open('/home/ubuntu/leads.csv', 'r') as f:
    reader = csv.DictReader(f)
    companies = []
    for row in reader:
        if row.get('Website'):
            domain = row['Website'].replace('http://', '').replace('https://', '').split('/')[0]
            companies.append(domain)
    # Return top 50 unique domains
    seen = set()
    for d in companies:
        if d and d not in seen:
            seen.add(d)
            print(d)
        if len(seen) >= 50:
            break
" > "${STATE_DIR}/seed_domains_${date_stamp}.txt"
    
    local count=$(wc -l < "${STATE_DIR}/seed_domains_${date_stamp}.txt")
    log "Extracted ${count} seed domains for lookalike expansion"
}

# Run lookalike expansion via Exa/Parallel.ai (if keys available)
run_lookalike_expansion() {
    local date_stamp=$1
    local run_log=$2
    log "=== Lookalike Expansion ==="
    
    if [[ -z "${EXA_API_KEY:-}" && -z "${PARALLEL_AI_API_KEY:-}" ]]; then
        log "Skipping lookalike - EXA_API_KEY and PARALLEL_AI_API_KEY not set"
        return 0
    fi
    
    get_seed_companies "$date_stamp"
    
    if [[ -n "${EXA_API_KEY:-}" ]]; then
        log "Running Exa findSimilar..."
        /usr/bin/python3 "${SCRIPT_DIR}/exa_lookalike.py" \
            --seeds "${STATE_DIR}/seed_domains_${date_stamp}.txt" \
            --output "${STATE_DIR}/exa_lookalike_${date_stamp}.json" \
            2>&1 | tee -a "${run_log}"
    fi
    
    if [[ -n "${PARALLEL_AI_API_KEY:-}" ]]; then
        log "Running Parallel AI lookalike..."
        /usr/bin/python3 "${SCRIPT_DIR}/parallel_lookalike.py" \
            --seeds "${STATE_DIR}/seed_domains_${date_stamp}.txt" \
            --output "${STATE_DIR}/parallel_lookalike_${date_stamp}.json" \
            2>&1 | tee -a "${run_log}"
    fi
}

# Deep Google Maps sweep (all tier1 + tier2 locations, all categories)
run_deep_maps_sweep() {
    local date_stamp=$1
    local run_log=$2
    log "=== Deep Google Maps Sweep ==="
    
    /usr/bin/python3 "${SCRIPT_DIR}/google_maps_scrape.py" \
        --config "${CONFIG}" \
        --limit 1000 \
        --output "${STATE_DIR}/gmaps_deep_${date_stamp}.json" \
        --deep-sweep \
        2>&1 | tee -a "${run_log}"
}

# Prospeo industry-wide sweeps
run_prospeo_industry_sweep() {
    local date_stamp=$1
    local run_log=$2
    log "=== Prospeo Industry Sweep ==="
    
    if [[ -z "${PROSPEO_API_KEY:-}" ]]; then
        log "Skipping Prospeo sweep - PROSPEO_API_KEY not set"
        return 0
    fi
    
    /usr/bin/python3 "${SCRIPT_DIR}/prospeo_industry_sweep.py" \
        --config "${CONFIG}" \
        --output "${STATE_DIR}/prospeo_industry_${date_stamp}.json" \
        2>&1 | tee -a "${run_log}"
}

# Apollo lookalike from seed companies
run_apollo_lookalike() {
    local date_stamp=$1
    local run_log=$2
    log "=== Apollo Lookalike ==="
    
    if [[ -z "${APOLLO_API_KEY:-}" ]]; then
        log "Skipping Apollo lookalike - APOLLO_API_KEY not set"
        return 0
    fi
    
    get_seed_companies "$date_stamp"
    
    /usr/bin/python3 "${SCRIPT_DIR}/apollo_lookalike.py" \
        --seeds "${STATE_DIR}/seed_domains_${date_stamp}.txt" \
        --output "${STATE_DIR}/apollo_lookalike_${date_stamp}.json" \
        2>&1 | tee -a "${run_log}"
}

# Merge all weekly sources
run_weekly_merge() {
    local date_stamp=$1
    local run_log=$2
    log "=== Weekly Merge & Qualify ==="
    
    /usr/bin/python3 "${SCRIPT_DIR}/weekly_merge_qualify.py" \
        --config "${CONFIG}" \
        --date "${date_stamp}" \
        --output "${STATE_DIR}/weekly_qualified_${date_stamp}.csv" \
        2>&1 | tee -a "${run_log}"
}