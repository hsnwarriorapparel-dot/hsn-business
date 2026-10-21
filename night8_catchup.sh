#!/bin/bash
# Day 8 catch-up chain: hunt -> pipeline -> excel rebuild -> git commit
# Launched detached 2026-10-21 ~00:30 UTC after the 20:00 UTC cron session died early.
PY=/home/ubuntu/.hermes/tools/python-3.14.7+20260901-linux-arm64/bin/python3
cd /home/ubuntu

echo "$(date -u '+%H:%M:%S') CHAIN START (day8 catch-up)" >> /home/ubuntu/day8_log.txt

# Phase A: hunt until 100 ammo
$PY /home/ubuntu/day8_hunt.py >> /home/ubuntu/day8_log.txt 2>&1
HUNT_RC=$?
echo "$(date -u '+%H:%M:%S') hunt finished rc=$HUNT_RC" >> /home/ubuntu/day8_log.txt

if [ $HUNT_RC -ne 0 ]; then
    echo "$(date -u '+%H:%M:%S') hunt rc=$HUNT_RC — retrying once" >> /home/ubuntu/day8_log.txt
    $PY /home/ubuntu/day8_hunt.py >> /home/ubuntu/day8_log.txt 2>&1
    echo "$(date -u '+%H:%M:%S') hunt retry rc=$?" >> /home/ubuntu/day8_log.txt
fi

# Phase B: pipeline (emails -> WA 10 -> IG)
$PY /home/ubuntu/day8_pipeline.py >> /home/ubuntu/day8_log.txt 2>&1
echo "$(date -u '+%H:%M:%S') pipeline finished rc=$?" >> /home/ubuntu/day8_log.txt

# Phase C: Excel rebuild + WA pending list
$PY /home/ubuntu/rebuild_tracker.py >> /home/ubuntu/day8_log.txt 2>&1
$PY /home/ubuntu/make_wa_excel.py >> /home/ubuntu/day8_log.txt 2>&1
echo "$(date -u '+%H:%M:%S') excel rebuilt rc=$?" >> /home/ubuntu/day8_log.txt

# Phase D: git commit + push
export GIT_SSH_COMMAND="ssh -i /home/ubuntu/.ssh/hsn_backup_key -o StrictHostKeyChecking=no -o IdentitiesOnly=yes"
cd /home/ubuntu/business-backup
cp -u /home/ubuntu/leads.csv /home/ubuntu/HWA_Lead_Tracker.xlsx /home/ubuntu/WA_Pending_List.xlsx . 2>/dev/null
cp -u /home/ubuntu/day8_*.py /home/ubuntu/night8_catchup.sh . 2>/dev/null
git add -A
git diff --cached --quiet || git commit -q -m "Day 8 catch-up: hunt + pipeline after 20:00 UTC session died early (0 leads hunted then)" && git push -q origin main
echo "$(date -u '+%H:%M:%S') git pushed rc=$?" >> /home/ubuntu/day8_log.txt

echo "$(date -u '+%H:%M:%S') CHAIN DONE" >> /home/ubuntu/day8_log.txt
