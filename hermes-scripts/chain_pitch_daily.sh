#!/bin/bash
# Chain / franchise corporate pitch runner (cron: 25 20 * * *).
#
# Runs AFTER the first-touch wave (0 20 * * *) so the day's 100 cold-email
# quota is already spent and the chain pitches never push us over it. The
# chain pitches are a separate, higher-value action (corporate/franchise
# buyers), and they are quota-aware: the script refuses to send if the daily
# email quota is already reached.
#
# One corporate email per brand can win every location: TITLE Boxing Club
# alone runs 146 locations and we had been emailing each one separately.
set -u
PY=$(ls -d /home/ubuntu/.hermes/tools/python-3*/bin/python3 2>/dev/null | sort -V | tail -1)
if [ -z "$PY" ]; then echo "interpreter not found"; exit 1; fi
LOG=/home/ubuntu/day23_chain_pitch_log.txt

echo "=== chain pitch run $(date -u '+%Y-%m-%d %H:%M:%S UTC') ==="

# Respect the daily email quota. Use the shared LEDGER (counts actual EMAILS,
# not tracker rows - a chain pitch stamps every location row of a brand, which
# inflated the old CSV counter up to 13x).
SENT=$("$PY" -c "import sys; sys.path.insert(0,'/home/ubuntu'); from outreach_quota import sent_today; print(sent_today())")
CAP=$("$PY" -c "import sys; sys.path.insert(0,'/home/ubuntu'); from outreach_quota import chain_allowance; print(chain_allowance())")
echo "emails sent today: ${SENT} / 100 quota | chain pitches left: ${CAP}"

if [ "${SENT:-0}" -ge 100 ]; then
  echo "QUOTA REACHED - chain pitches deferred to the next day (they are draft-only until the quota frees up)"
  exit 0
fi
if [ "${CAP:-0}" -le 0 ]; then
  echo "CHAIN RESERVE ALREADY USED TODAY - nothing more to send"
  exit 0
fi

# Auto-detect the newest dayNN engine so this wrapper never goes stale when
# tomorrow's day25 files appear (the old hardcoded day23/day24 path would have
# run yesterday's engine, with yesterday's quota accounting).
ENGINE="$(ls -1t /home/ubuntu/day*_chain_pitch.py 2>/dev/null | head -1)"
if [ -z "$ENGINE" ]; then echo "no chain pitch engine found"; exit 1; fi
echo "engine: $ENGINE"

"$PY" "$ENGINE" --send 2>&1 | tee -a "$LOG"
exit 0
