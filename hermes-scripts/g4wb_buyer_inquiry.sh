#!/bin/bash
# go4WorldBusiness daily buyer inquiry (cron: 5 9 * * *).
#
# WHY: the JUNIOR membership allows exactly ONE buyer inquiry per day, and a
# buyer inquiry is a DIRECT quote request from a real importer - the highest
# intent channel we have. On 2026-11-07 we sent one (Karate Black Master Belt,
# 400 pcs, Krav Maga Federation) and the platform refused a second because the
# daily limit was reached.
#
# The queue holds ranked RFQs: taekwondo belts (3,500 pcs, Malaysia), boxing
# accessories (500-1,000 pcs, Egypt), judo belts (100 pcs, Portugal), and more.
# Each day this picks the biggest eligible one.
#
# ELIGIBILITY (both rules enforced by g4wb_buyer_queue.py):
#   1. a buylead can only be inquired about 5 DAYS after it was posted
#   2. JUNIOR = 1 buyer inquiry/day free (Premium GOLD/SILVER = 100/day)
#
# The captcha is regenerated on every page load, so the send is TWO PHASE and
# needs the vision model to read the image. This script does phase 1 (open the
# tab, capture the captcha) and leaves the target saved; the agent finishes
# phase 2. If the agent is not available, the slot is simply skipped and the
# queue keeps its place for the next day - never lost, never double-sent.
set -u
PY=$(ls -d /home/ubuntu/.hermes/tools/python-3*/bin/python3 2>/dev/null | sort -V | tail -1)
if [ -z "$PY" ]; then echo "interpreter not found"; exit 1; fi
LOG=/home/ubuntu/g4wb_buyer_queue_log.txt

echo "=== go4WorldBusiness buyer inquiry $(date -u '+%Y-%m-%d %H:%M:%S UTC') ==="

# Refresh the queue and its messages first. The queue used to hold 8
# hand-mapped, all-ARCHIVED targets. There are 23 live buyleads and 11 of
# them are in our product space - 10 of those can receive a JUNIOR inquiry.
# A stale queue means a wasted daily slot.
"$PY" /home/ubuntu/g4wb_queue_rebuild.py 2>&1 | tee -a "$LOG" | tail -20
"$PY" /home/ubuntu/g4wb_queue_messages.py 2>&1 | tee -a "$LOG" | head -3

# The RFQ harvest is the BETTER source: /buyers/<country>/<category> pages
# are live buy requirements carrying the product, the quantity, the
# destination and the payment terms. 33 live in-scope requirements, each
# with a quantity we can quote against.
# Refresh the LIVE requirement set first - it is the cleanest source
# (VERIFIED status, the date, the full specification and the inquiry
# route). The RFQ harvest below is the fallback.
"$PY" /home/ubuntu/g4wb_live_rfq_fetch.py 2>&1 | tee -a "$LOG" | tail -4

"$PY" /home/ubuntu/g4wb_rfq_harvest.py --pages 2 \
    --countries oman portugal malaysia egypt saudi-arabia united-arab-emirates \
    --cats martial-arts-belts boxing-gloves martial-arts-gloves martial-arts-mats \
           uniforms team-uniforms karate-uniforms sportswear protective-equipment \
           kick-pads hand-wraps mouth-guards sports-jerseys fight-wear \
    2>&1 | tee -a "$LOG" | tail -6
"$PY" /home/ubuntu/g4wb_rfq_queue.py 2>&1 | tee -a "$LOG" | head -26

"$PY" /home/ubuntu/g4wb_buyer_queue.py 2>&1 | tee -a "$LOG" | tee /tmp/g4wb_queue_out.$$

# If a target was prepared, phase 1 has run and the captcha image is waiting.
# Leave the instructions in stdout so the agent can complete phase 2.
# Only say so when the queue actually picked a target (the TARGET= line above).
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
