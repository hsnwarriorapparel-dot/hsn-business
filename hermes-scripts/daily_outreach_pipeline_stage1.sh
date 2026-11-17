#!/bin/bash
# Stage 1: Ammo top-up hunt (runs 0 20 * * * = 1:00 AM PKT)
# Only runs if ammo < 100. Completes in ~5-15 min.
set -u
PY=$(ls -d /home/ubuntu/.hermes/tools/python-3*/bin/python3 2>/dev/null | sort -V | tail -1)
if [ -z "$PY" ]; then echo "interpreter not found"; exit 1; fi
LOG=/home/ubuntu/outreach_pipeline.log

echo "=== daily outreach pipeline STAGE 1 - AMMO TOP-UP $(date -u '+%Y-%m-%d %H:%M:%S UTC') ===" | tee -a "$LOG"

# Ensure today's quota state exists
"$PY" /home/ubuntu/ensure_quota_state.py 2>&1 | tee -a "$LOG"

# Check ammo and hunt if needed
"$PY" -c "
import csv
with open('/home/ubuntu/leads.csv', newline='', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))
n = 0
for r in rows:
    st = (r.get('Status') or '').lower()
    if 'email sent' in st or 'failed' in st or 'excluded' in st or 're-hunt' in st:
        continue
    e = (r.get('Email') or '').strip()
    if e and '@' in e and '.' in e.split('@')[-1]:
        n += 1
print(f'ammo: {n}')
with open('/home/ubuntu/outreach_pipeline.log', 'a') as f:
    f.write(f'ammo before hunt: {n}\\n')
" 2>&1 | tee -a "$LOG"

AMMO=$(python3 -c "
import csv
with open('/home/ubuntu/leads.csv', newline='', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))
n = 0
for r in rows:
    st = (r.get('Status') or '').lower()
    if 'email sent' in st or 'failed' in st or 'excluded' in st or 're-hunt' in st:
        continue
    e = (r.get('Email') or '').strip()
    if e and '@' in e and '.' in e.split('@')[-1]:
        n += 1
print(n)
")

if [ "$AMMO" -lt 100 ]; then
    echo "ammo below 100 ($AMMO) - running top-up hunt" | tee -a "$LOG"
    timeout 2400 "$PY" /home/ubuntu/day24_ammo_hunt.py 2>&1 | tee -a "$LOG"
else
    echo "ammo sufficient ($AMMO) - skipping hunt" | tee -a "$LOG"
fi

echo "=== STAGE 1 COMPLETE ===" | tee -a "$LOG"
exit 0
