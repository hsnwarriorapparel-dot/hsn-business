#!/bin/bash
# DAY 5 USA NIGHT SYSTEM — 1:00 AM PKT (20:00 UTC Oct 15)
# USA leads: hunt 200 emails -> email waves -> IG follow+DM all -> max 10 WA
TARGET=$(date -u -d "2026-10-15 20:00" +%s)
while [ $(date -u +%s) -lt $TARGET ]; do sleep 60; done
echo "Day 5 USA kickoff at $(date -u)" >> /home/ubuntu/day5_log.txt

PY=/home/ubuntu/.hermes/tools/python-3.14.7+20260901-linux-arm64/bin/python3
cd /home/ubuntu

# 1. Hunter (finds 200 USA leads, safe-write append)
nohup $PY /home/ubuntu/day5_usa_hunter.py >> /home/ubuntu/day5_hunter_stdout.txt 2>&1 &
HUNTER_PID=$!
echo "Hunter PID $HUNTER_PID" >> /home/ubuntu/day5_log.txt

# 2. Monitor + restart if died before 200 (max 4 restarts)
restarts=0
while [ $restarts -lt 4 ]; do
  sleep 1800
  if ! kill -0 $HUNTER_PID 2>/dev/null; then
    D5=$(grep -c "Day 5 USA" /home/ubuntu/leads.csv 2>/dev/null || echo 0)
    if [ "$D5" -lt 200 ]; then
      restarts=$((restarts+1))
      echo "Hunter died ($D5/200). Restart #$restarts $(date -u)" >> /home/ubuntu/day5_log.txt
      nohup $PY /home/ubuntu/day5_usa_hunter.py --resume >> /home/ubuntu/day5_hunter_stdout.txt 2>&1 &
      HUNTER_PID=$!
    else
      echo "Hunter complete: $D5 leads $(date -u)" >> /home/ubuntu/day5_log.txt
      break
    fi
  fi
done
echo "DAY5 HUNT PHASE DONE $(date -u)" >> /home/ubuntu/day5_log.txt
