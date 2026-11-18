#!/bin/bash
# Shudokan Follow-up 4 nudge (cron: 0 9 20 11 *)
# If no reply to volume/fabric/logo request, send nudge
set -u
LOG=/home/ubuntu/shudokan_nudge_log.txt

echo "=== Shudokan nudge $(date -u '+%Y-%m-%d %H:%M:%S UTC') ===" | tee -a "$LOG"

# Check if replied since Nov 17
if grep -q "L183" /home/ubuntu/leads.csv | grep -q "REPLIED.*2026-11-1[89]\|REPLIED.*2026-11-2[0-9]"; then
    echo "Shudokan already replied - skipping nudge" | tee -a "$LOG"
    exit 0
fi

# Send nudge email (user will copy-paste)
cat > /home/ubuntu/shudokan_nudge_email.txt << 'EOF'
Subject: Shudokan — any questions on the catalog?

Hola,

Just checking — did the price list and catalog arrive OK?

Happy to answer any questions on specs, fabrics, or minimums. No pressure — just here if you need anything.

Saludos,
HSN Warrior Apparels
+92 337 333 6381
https://hsnwarriorapparels.vercel.app
EOF

echo "Nudge email drafted at /home/ubuntu/shudokan_nudge_email.txt" | tee -a "$LOG"

# Also create WA nudge
cat > /home/ubuntu/shudokan_nudge_wa.txt << 'EOF'
Hola! 👋 Just checking — did the catalog arrive OK? Happy to answer any questions on specs, fabrics, or minimums. No pressure — just here if you need anything.

— HSN Warrior Apparels
+92 337 333 6381
https://hsnwarriorapparels.vercel.app
EOF

echo "Nudge WA drafted at /home/ubuntu/shudokan_nudge_wa.txt" | tee -a "$LOG"
exit 0