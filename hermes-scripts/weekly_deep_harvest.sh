#!/usr/bin/env bash
# =============================================================================
# WEEKLY DEEP HARVEST - Exhaustive lead discovery (Sunday 02:00 UTC)
# =============================================================================
# Runs lookalike expansion, keyword mining, and deep source sweeps
# =============================================================================

set -euo pipefail

LIB_DIR="/home/ubuntu/lead_gen_system/scripts"
LOG_DIR="/home/ubuntu/lead_gen_system/logs"
DATE_STAMP=$(date -u +"%Y%m%d_%H%M%S")
RUN_LOG="${LOG_DIR}/weekly_harvest_${DATE_STAMP}.log"

mkdir -p "${LOG_DIR}"

log() {
    echo "[$(date -u +"%Y-%m-%d %H:%M:%S UTC")] $*" | tee -a "${RUN_LOG}"
}

# Source the library
source "${LIB_DIR}/weekly_harvest_lib.sh"

# Main
main() {
    log "=========================================="
    log "WEEKLY DEEP HARVEST STARTED"
    log "Date: $(date -u)"
    log "Run ID: ${DATE_STAMP}"
    log "=========================================="
    
    # Run phases (can take longer since weekly)
    timeout 1800 bash -c "source ${LIB_DIR}/weekly_harvest_lib.sh && run_lookalike_expansion ${DATE_STAMP} ${RUN_LOG}" || log "Lookalike expansion timed out"
    timeout 1800 bash -c "source ${LIB_DIR}/weekly_harvest_lib.sh && run_deep_maps_sweep ${DATE_STAMP} ${RUN_LOG}" || log "Deep maps sweep timed out"
    timeout 1800 bash -c "source ${LIB_DIR}/weekly_harvest_lib.sh && run_prospeo_industry_sweep ${DATE_STAMP} ${RUN_LOG}" || log "Prospeo industry sweep timed out"
    timeout 1800 bash -c "source ${LIB_DIR}/weekly_harvest_lib.sh && run_apollo_lookalike ${DATE_STAMP} ${RUN_LOG}" || log "Apollo lookalike timed out"
    timeout 1800 bash -c "source ${LIB_DIR}/weekly_harvest_lib.sh && run_weekly_merge ${DATE_STAMP} ${RUN_LOG}" || log "Weekly merge timed out"
    
    log "=========================================="
    log "WEEKLY DEEP HARVEST COMPLETED"
    log "Run ID: ${DATE_STAMP}"
    log "Log: ${RUN_LOG}"
    log "=========================================="
}

main "$@"