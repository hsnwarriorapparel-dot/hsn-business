#!/usr/bin/env bash
# =============================================================================
# DAILY LEAD GENERATION PIPELINE - HSN Warrior Apparels
# =============================================================================
# Runs daily at 06:00 UTC (11:00 PKT) via cron
# Multi-source lead discovery -> AI qualification -> email validation -> outreach feed
# =============================================================================

set -euo pipefail

# Load configuration
CONFIG="/home/ubuntu/lead_gen_system/icp_config.yaml"
SCRIPT_DIR="/home/ubuntu/lead_gen_system/scripts"
LOG_DIR="/home/ubuntu/lead_gen_system/logs"
STATE_DIR="/home/ubuntu/lead_gen_system/state"
DATE_STAMP=$(date -u +"%Y%m%d_%H%M%S")
RUN_LOG="${LOG_DIR}/lead_gen_${DATE_STAMP}.log"

# Use the correct Python interpreter
PYTHON="/usr/bin/python3"

mkdir -p "${LOG_DIR}" "${STATE_DIR}"

# Logging function
log() {
    echo "[$(date -u +"%Y-%m-%d %H:%M:%S UTC")] $*" | tee -a "${RUN_LOG}"
}

error() {
    log "ERROR: $*"
    exit 1
}

# Check required API keys
check_api_keys() {
    log "Checking API keys..."
    local missing=()
    [[ -z "${APOLLO_API_KEY:-}" ]] && missing+=("APOLLO_API_KEY")
    [[ -z "${PROSPEO_API_KEY:-}" ]] && missing+=("PROSPEO_API_KEY")
    [[ -z "${OPENAI_API_KEY:-}" ]] && missing+=("OPENAI_API_KEY")
    [[ -z "${MILLIONVERIFIER_API_KEY:-}" ]] && missing+=("MILLIONVERIFIER_API_KEY")
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log "WARNING: Missing API keys: ${missing[*]}"
        log "Some lead sources will be skipped. Add keys to environment to enable."
    else
        log "All required API keys present"
    fi
}

# Parse YAML config (simple grep-based for bash)
get_config() {
    local key="$1"
    grep "^${key}:" "${CONFIG}" | head -1 | sed 's/^[^:]*: *//' | sed 's/ *#.*//'
}

# =============================================================================
# PHASE 1: APOLLO PROSPECTING (ICP -> Decision Makers)
# =============================================================================
run_apollo_prospect() {
    log "=== PHASE 1: Apollo Prospecting ==="
    
    if [[ -z "${APOLLO_API_KEY:-}" ]]; then
        log "Skipping Apollo - APOLLO_API_KEY not set"
        return 0
    fi
    
    local daily_limit=$(grep "daily_limit:" "${CONFIG}" | head -1 | awk '{print $2}')
    local output_file="${STATE_DIR}/apollo_raw_${DATE_STAMP}.json"
    
    log "Running Apollo prospecting (limit: ${daily_limit})..."
    
    # Use the Apollo prospect skill via Python
    "${PYTHON}" "${SCRIPT_DIR}/apollo_prospect.py" \
        --config "${CONFIG}" \
        --limit "${daily_limit}" \
        --output "${output_file}" \
        2>&1 | tee -a "${RUN_LOG}"
    
    local exit_code=${PIPESTATUS[0]}
    if [[ ${exit_code} -eq 0 ]]; then
        local count=$(jq '.leads | length' "${output_file}" 2>/dev/null || echo 0)
        log "Apollo: Found ${count} leads"
    else
        log "Apollo prospecting failed with exit code ${exit_code}"
    fi
}

# =============================================================================
# PHASE 2: PROSPEO DISCOVERY (Company Search + Contact Enrichment)
# =============================================================================
run_prospeo_discovery() {
    log "=== PHASE 2: Prospeo Discovery ==="
    
    if [[ -z "${PROSPEO_API_KEY:-}" ]]; then
        log "Skipping Prospeo - PROSPEO_API_KEY not set"
        return 0
    fi
    
    local daily_limit=$(grep "daily_limit:" "${CONFIG}" | sed -n '2p' | awk '{print $2}')
    local output_file="${STATE_DIR}/prospeo_raw_${DATE_STAMP}.json"
    
    log "Running Prospeo discovery (limit: ${daily_limit})..."
    
    "${PYTHON}" "${SCRIPT_DIR}/prospeo_discovery.py" \
        --config "${CONFIG}" \
        --limit "${daily_limit}" \
        --output "${output_file}" \
        2>&1 | tee -a "${RUN_LOG}"
    
    local exit_code=${PIPESTATUS[0]}
    if [[ ${exit_code} -eq 0 ]]; then
        local count=$(jq '.companies | length' "${output_file}" 2>/dev/null || echo 0)
        log "Prospeo: Found ${count} companies"
    else
        log "Prospeo discovery failed with exit code ${exit_code}"
    fi
}

# =============================================================================
# PHASE 3: GOOGLE MAPS SCRAPE (Local Gym/Club Discovery)
# =============================================================================
run_google_maps() {
    log "=== PHASE 3: Google Maps Scrape ==="
    
    local daily_limit=$(grep "daily_limit:" "${CONFIG}" | sed -n '3p' | awk '{print $2}')
    local output_file="${STATE_DIR}/gmaps_raw_${DATE_STAMP}.json"
    
    log "Running Google Maps scrape (limit: ${daily_limit})..."
    
    "${PYTHON}" "${SCRIPT_DIR}/google_maps_scrape.py" \
        --config "${CONFIG}" \
        --limit "${daily_limit}" \
        --output "${output_file}" \
        2>&1 | tee -a "${RUN_LOG}"
    
    local exit_code=${PIPESTATUS[0]}
    if [[ ${exit_code} -eq 0 ]]; then
        local count=$(jq '.places | length' "${output_file}" 2>/dev/null || echo 0)
        log "Google Maps: Found ${count} places"
    else
        log "Google Maps scrape failed with exit code ${exit_code}"
    fi
}

# =============================================================================
# PHASE 4: G4WB BUYER INQUIRY (Existing - Rotating Countries)
# =============================================================================
run_g4wb_buyer() {
    log "=== PHASE 4: G4WB Buyer Inquiry ==="
    
    # This is handled by existing cron job g4wb_buyer_inquiry_batched.sh
    # Just verify it ran and collect results
    local latest_output=$(ls -t /home/ubuntu/.hermes/cron/output/g4wb-buyer-inquiry-batched_*.out 2>/dev/null | head -1)
    if [[ -n "${latest_output}" ]]; then
        log "G4WB buyer inquiry output: ${latest_output}"
        tail -20 "${latest_output}" | tee -a "${RUN_LOG}"
    else
        log "No recent G4WB buyer inquiry output found"
    fi
}

# =============================================================================
# PHASE 5: G4WB DIRECTORY FUNNEL (Existing - Screening)
# =============================================================================
run_g4wb_directory() {
    log "=== PHASE 5: G4WB Directory Funnel ==="
    
    local latest_output=$(ls -t /home/ubuntu/.hermes/cron/output/g4wb-buyer-directory-funnel-fixed_*.out 2>/dev/null | head -1)
    if [[ -n "${latest_output}" ]]; then
        log "G4WB directory funnel output: ${latest_output}"
        tail -20 "${latest_output}" | tee -a "${RUN_LOG}"
    else
        log "No recent G4WB directory funnel output found"
    fi
}

# =============================================================================
# PHASE 6: MERGE & DEDUP (Combine all sources)
# =============================================================================
run_merge_dedup() {
    log "=== PHASE 6: Merge & Deduplicate ==="
    
    local output_file="${STATE_DIR}/merged_${DATE_STAMP}.csv"
    
    "${PYTHON}" "${SCRIPT_DIR}/merge_dedup.py" \
        --config "${CONFIG}" \
        --date "${DATE_STAMP}" \
        --output "${output_file}" \
        2>&1 | tee -a "${RUN_LOG}"
    
    local exit_code=${PIPESTATUS[0]}
    if [[ ${exit_code} -eq 0 ]]; then
        local count=$(wc -l < "${output_file}")
        log "Merge: ${count} total unique leads (including header)"
    else
        log "Merge failed with exit code ${exit_code}"
    fi
}

# =============================================================================
# PHASE 7: AI QUALIFICATION (Judge each lead)
# =============================================================================
run_qualification() {
    log "=== PHASE 7: AI Qualification ==="
    
    if [[ -z "${OPENAI_API_KEY:-}" ]]; then
        log "Skipping qualification - OPENAI_API_KEY not set"
        return 0
    fi
    
    local input_file="${STATE_DIR}/merged_${DATE_STAMP}.csv"
    local output_file="${STATE_DIR}/qualified_${DATE_STAMP}.csv"
    
    log "Running AI qualification..."
    
    "${PYTHON}" "${SCRIPT_DIR}/qualify_leads.py" \
        --config "${CONFIG}" \
        --input "${input_file}" \
        --output "${output_file}" \
        2>&1 | tee -a "${RUN_LOG}"
    
    local exit_code=${PIPESTATUS[0]}
    if [[ ${exit_code} -eq 0 ]]; then
        local total=$(wc -l < "${output_file}")
        local qualified=$(grep -c "STRONG\|GOOD\|PARTIAL" "${output_file}" 2>/dev/null || echo 0)
        log "Qualification: ${qualified}/${total} leads qualified"
    else
        log "Qualification failed with exit code ${exit_code}"
    fi
}

# =============================================================================
# PHASE 8: WEBSITE VERIFICATION (Live site check)
# =============================================================================
run_website_verify() {
    log "=== PHASE 8: Website Verification ==="
    
    local input_file="${STATE_DIR}/qualified_${DATE_STAMP}.csv"
    local output_file="${STATE_DIR}/verified_${DATE_STAMP}.csv"
    
    log "Running website verification..."
    
    "${PYTHON}" "${SCRIPT_DIR}/verify_websites.py" \
        --config "${CONFIG}" \
        --input "${input_file}" \
        --output "${output_file}" \
        2>&1 | tee -a "${RUN_LOG}"
    
    local exit_code=${PIPESTATUS[0]}
    if [[ ${exit_code} -eq 0 ]]; then
        local total=$(wc -l < "${output_file}")
        local live=$(grep -c "LIVE" "${output_file}" 2>/dev/null || echo 0)
        log "Website verify: ${live}/${total} sites live"
    else
        log "Website verification failed with exit code ${exit_code}"
    fi
}

# =============================================================================
# PHASE 9: EMAIL VALIDATION (MillionVerifier)
# =============================================================================
run_email_validation() {
    log "=== PHASE 9: Email Validation ==="
    
    if [[ -z "${MILLIONVERIFIER_API_KEY:-}" ]]; then
        log "Skipping email validation - MILLIONVERIFIER_API_KEY not set"
        return 0
    fi
    
    local input_file="${STATE_DIR}/verified_${DATE_STAMP}.csv"
    local output_file="${STATE_DIR}/validated_${DATE_STAMP}.csv"
    
    log "Running email validation..."
    
    "${PYTHON}" "${SCRIPT_DIR}/validate_emails.py" \
        --config "${CONFIG}" \
        --input "${input_file}" \
        --output "${output_file}" \
        2>&1 | tee -a "${RUN_LOG}"
    
    local exit_code=${PIPESTATUS[0]}
    if [[ ${exit_code} -eq 0 ]]; then
        local total=$(wc -l < "${output_file}")
        local valid=$(grep -c "VALID" "${output_file}" 2>/dev/null || echo 0)
        log "Email validation: ${valid}/${total} emails valid"
    else
        log "Email validation failed with exit code ${exit_code}"
    fi
}

# =============================================================================
# PHASE 10: FEED OUTREACH PIPELINE (Add to leads.csv / Smartlead)
# =============================================================================
run_pipeline_feed() {
    log "=== PHASE 10: Feed Outreach Pipeline ==="
    
    local input_file="${STATE_DIR}/validated_${DATE_STAMP}.csv"
    local output_file="/home/ubuntu/lead_gen_system/leads_outreach_ready.csv"
    
    log "Feeding qualified leads to outreach pipeline..."
    
    "${PYTHON}" "${SCRIPT_DIR}/feed_pipeline.py" \
        --config "${CONFIG}" \
        --input "${input_file}" \
        --output "${output_file}" \
        --master-leads "/home/ubuntu/leads.csv" \
        2>&1 | tee -a "${RUN_LOG}"
    
    local exit_code=${PIPESTATUS[0]}
    if [[ ${exit_code} -eq 0 ]]; then
        local count=$(wc -l < "${output_file}" 2>/dev/null || echo 0)
        log "Pipeline feed: ${count} new leads ready for outreach"
    else
        log "Pipeline feed failed with exit code ${exit_code}"
    fi
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================
main() {
    log "=========================================="
    log "DAILY LEAD GENERATION PIPELINE STARTED"
    log "Date: $(date -u)"
    log "Run ID: ${DATE_STAMP}"
    log "=========================================="
    
    check_api_keys
    
    # Run phases sequentially with individual timeouts via subshells
    timeout 600 bash -c "source /home/ubuntu/lead_gen_system/scripts/daily_lead_gen_pipeline.sh && run_apollo_prospect" || log "Phase 1 timed out or failed"
    timeout 600 bash -c "source /home/ubuntu/lead_gen_system/scripts/daily_lead_gen_pipeline.sh && run_prospeo_discovery" || log "Phase 2 timed out or failed"
    timeout 600 bash -c "source /home/ubuntu/lead_gen_system/scripts/daily_lead_gen_pipeline.sh && run_google_maps" || log "Phase 3 timed out or failed"
    timeout 60 bash -c "source /home/ubuntu/lead_gen_system/scripts/daily_lead_gen_pipeline.sh && run_g4wb_buyer" || log "Phase 4 timed out or failed"
    timeout 60 bash -c "source /home/ubuntu/lead_gen_system/scripts/daily_lead_gen_pipeline.sh && run_g4wb_directory" || log "Phase 5 timed out or failed"
    
    # Sequential phases (depend on previous)
    timeout 120 bash -c "source /home/ubuntu/lead_gen_system/scripts/daily_lead_gen_pipeline.sh && run_merge_dedup" || log "Phase 6 timed out or failed"
    timeout 600 bash -c "source /home/ubuntu/lead_gen_system/scripts/daily_lead_gen_pipeline.sh && run_qualification" || log "Phase 7 timed out or failed"
    timeout 300 bash -c "source /home/ubuntu/lead_gen_system/scripts/daily_lead_gen_pipeline.sh && run_website_verify" || log "Phase 8 timed out or failed"
    timeout 300 bash -c "source /home/ubuntu/lead_gen_system/scripts/daily_lead_gen_pipeline.sh && run_email_validation" || log "Phase 9 timed out or failed"
    timeout 120 bash -c "source /home/ubuntu/lead_gen_system/scripts/daily_lead_gen_pipeline.sh && run_pipeline_feed" || log "Phase 10 timed out or failed"
    
    log "=========================================="
    log "DAILY LEAD GENERATION PIPELINE COMPLETED"
    log "Run ID: ${DATE_STAMP}"
    log "Log: ${RUN_LOG}"
    log "=========================================="
}

# Only run main if script is executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi