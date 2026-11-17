#!/bin/bash
# Batched g4wb buyer inquiry - runs daily at 9:05 AM UTC
# Rotates through country subsets to stay under 1 hour
set -u
PY=$(ls -d /home/ubuntu/.hermes/tools/python-3*/bin/python3 2>/dev/null | sort -V | tail -1)
if [ -z "$PY" ]; then echo "interpreter not found"; exit 1; fi
LOG=/home/ubuntu/g4wb_buyer_queue_log.txt

echo "=== go4WorldBusiness buyer inquiry BATCHED $(date -u '+%Y-%m-%d %H:%M:%S UTC') ===" | tee -a "$LOG"

# Refresh queue (fast - uses cached data)
timeout 300 "$PY" /home/ubuntu/g4wb_queue_rebuild.py 2>&1 | tee -a "$LOG" | tail -20
timeout 300 "$PY" /home/ubuntu/g4wb_queue_messages.py 2>&1 | tee -a "$LOG" | head -3

# Today's country subset (rotates daily based on day of month)
DAY=$(date -u +%d)
COUNTRIES=("oman" "united-arab-emirates" "saudi-arabia" "malaysia" "egypt" "portugal" "australia" "israel")
SUBSET_START=$(( (DAY - 1) % ${#COUNTRIES[@]} ))
SUBSET=${COUNTRIES[$SUBSET_START]}
echo "Today's country subset: $SUBSET" | tee -a "$LOG"

# Refresh LIVE RFQs for today's subset only
timeout 600 "$PY" /home/ubuntu/g4wb_live_rfq_fetch.py "$SUBSET" 2>&1 | tee -a "$LOG" | tail -4

# Harvest RFQs (fallback) - limit to 2 pages total
timeout 600 "$PY" /home/ubuntu/g4wb_rfq_harvest.py --pages 2 \
    --countries oman portugal malaysia egypt saudi-arabia united-arab-emirates \
    --cats martial-arts-belts boxing-gloves martial-arts-gloves martial-arts-mats \
           uniforms team-uniforms karate-uniforms sportswear protective-equipment \
           kick-pads hand-wraps mouth-guards sports-jerseys fight-wear \
    2>&1 | tee -a "$LOG" | tail -6
timeout 300 "$PY" /home/ubuntu/g4wb_rfq_queue.py 2>&1 | tee -a "$LOG" | head -26

# Run buyer queue (picks 1 inquiry, runs phase 1)
timeout 600 "$PY" /home/ubuntu/g4wb_buyer_queue.py 2>&1 | tee -a "$LOG" | tee /tmp/g4wb_queue_out.$$

if grep -q '^TARGET=' /tmp/g4wb_queue_out.$$ 2>/dev/null; then
  echo ""
  echo "PHASE 1 READY - captcha image at /home/ubuntu/g4wb_captcha.png"
  echo "Read it, then run: $PY /home/ubuntu/g4wb_inquiry_send.py <href> <captcha> [message_file]"
elif [ -f /home/ubuntu/g4wb_inquiry_target.json ] && grep -q '^TARGET=' /home/ubuntu/g4wb_queue_last_target 2>/dev/null; then
  echo ""
  echo "PHASE 1 READY - captcha image at /home/ubuntu/g4wb_captcha.png"
fi
rm -f /tmp/g4wb_queue_out.$$
exit 0
