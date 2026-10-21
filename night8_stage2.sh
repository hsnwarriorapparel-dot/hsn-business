#!/bin/bash
# Day 8 stage 2: wait for running pipeline IG pass -> hunt 100 fresh leads (FIXED script)
# -> IG follow+DM all fresh Day-8 leads -> rebuild Excel -> git commit.
PY=/home/ubuntu/.hermes/tools/python-3.14.7+20260901-linux-arm64/bin/python3
cd /home/ubuntu
L=/home/ubuntu/day8_log.txt

echo "$(date -u '+%H:%M:%S') STAGE2 START — waiting for running pipeline to exit" >> $L

# Wait for day8_pipeline.py to finish (max 40 min)
for i in $(seq 1 80); do
    pgrep -f "python3 /home/ubuntu/day8_pipeline.py" > /dev/null || break
    sleep 30
done
echo "$(date -u '+%H:%M:%S') pipeline exited — hunting (fixed next_id)" >> $L

# Hunt fresh leads until 100 ammo
$PY /home/ubuntu/day8_hunt.py >> $L 2>&1
echo "$(date -u '+%H:%M:%S') hunt rc=$?" >> $L

# IG follow + DM all fresh Day-8 leads
$PY /home/ubuntu/day8_ig_batch.py >> $L 2>&1
echo "$(date -u '+%H:%M:%S') ig batch rc=$?" >> $L

# Rebuild Excel + WA pending list
$PY /home/ubuntu/rebuild_tracker.py >> $L 2>&1
$PY /home/ubuntu/make_wa_excel.py >> $L 2>&1
echo "$(date -u '+%H:%M:%S') excel rebuilt rc=$?" >> $L

# Read-back verification
echo "$(date -u '+%H:%M:%S') VERIFY: $(grep -c 'Day 8' /home/ubuntu/leads.csv) Day-8 rows | $(wc -l < /home/ubuntu/leads.csv) total lines" >> $L

# Git commit + push
export GIT_SSH_COMMAND="ssh -i /home/ubuntu/.ssh/hsn_backup_key -o StrictHostKeyChecking=no -o IdentitiesOnly=yes"
cd /home/ubuntu/business-backup
cp -u /home/ubuntu/leads.csv /home/ubuntu/HWA_Lead_Tracker.xlsx /home/ubuntu/WA_Pending_List.xlsx . 2>/dev/null
cp -u /home/ubuntu/day8_hunt.py /home/ubuntu/day8_ig_batch.py /home/ubuntu/night8_stage2.sh . 2>/dev/null
git add -A
git diff --cached --quiet || { git commit -q -m "Day 8 fix-and-continue: hunt bug fixed (next_id), 100 ammo banked, IG follow+DM fresh leads" && git push -q origin main; }
echo "$(date -u '+%H:%M:%S') git rc=$?" >> $L

echo "$(date -u '+%H:%M:%S') STAGE2 DONE" >> $L
