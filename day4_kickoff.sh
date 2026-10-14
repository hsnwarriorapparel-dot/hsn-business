#!/bin/bash
# DAY 4 NIGHT SYSTEM — starts at 1:00 AM PKT (20:00 UTC Oct 14)
# Email-lead hunt (150-200) + email sending + IG fallback. NO WhatsApp (banned).
TARGET=$(date -u -d "2026-10-14 20:00" +%s)
while [ $(date -u +%s) -lt $TARGET ]; do sleep 60; done
echo "Day 4 kickoff at $(date -u)" >> /home/ubuntu/day4_log.txt

PY=/home/ubuntu/.hermes/tools/python-3.14.7+20260901-linux-arm64/bin/python3

# Start the hunter (finds leads with emails)
cd /home/ubuntu
nohup $PY /home/ubuntu/day4_email_hunter.py >> /home/ubuntu/day4_hunter_stdout.txt 2>&1 &
HUNTER_PID=$!
echo "Hunter started PID $HUNTER_PID at $(date -u)" >> /home/ubuntu/day4_log.txt

# Start the sender (waves every 30 min as leads appear)
sleep 300  # give hunter a 5-min head start
nohup $PY /home/ubuntu/day4_sender.py >> /home/ubuntu/day4_sender_stdout.txt 2>&1 &
SENDER_PID=$!
echo "Sender started PID $SENDER_PID at $(date -u)" >> /home/ubuntu/day4_log.txt

# Monitor loop: if hunter dies before finding 150, restart it (max 5 restarts)
restarts=0
while [ $restarts -lt 5 ]; do
  sleep 1800
  if ! kill -0 $HUNTER_PID 2>/dev/null; then
    COUNT=$(grep -c "^" /home/ubuntu/leads.csv 2>/dev/null || echo 0)
    # count day4 leads
    D4=$(grep -c "Day 4" /home/ubuntu/leads.csv 2>/dev/null || echo 0)
    if [ "$D4" -lt 150 ]; then
      restarts=$((restarts+1))
      echo "Hunter died with only $D4 leads. Restart #$restarts at $(date -u)" >> /home/ubuntu/day4_log.txt
      nohup $PY /home/ubuntu/day4_email_hunter.py --resume >> /home/ubuntu/day4_hunter_stdout.txt 2>&1 &
      HUNTER_PID=$!
    else
      echo "Hunter finished with $D4 leads at $(date -u)" >> /home/ubuntu/day4_log.txt
      break
    fi
  fi
done
echo "DAY4 KICKOFF MONITOR DONE at $(date -u)" >> /home/ubuntu/day4_log.txt
