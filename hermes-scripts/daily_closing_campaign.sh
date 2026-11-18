#!/bin/bash
# DAILY CLOSING CAMPAIGN — runs 09:00 UTC (2 PM PKT)
# Rotates through hot leads, escalates pressure, stops when one closes
set -u
LOG=/home/ubuntu/closing_campaign_log.txt
DATE=$(date -u '+%Y-%m-%d %H:%M:%S UTC')

echo "=== CLOSING CAMPAIGN $DATE ===" | tee -a "$LOG"

# Check if any lead already closed (signed PO/deposit)
if grep -q "SIGNED PO\|DEPOSIT RECEIVED\|DEAL CLOSED\|PO RECEIVED" /home/ubuntu/leads.csv; then
    echo "✅ CLIENT CLOSED - campaign stopping" | tee -a "$LOG"
    exit 0
fi

# HOT LEADS ARRAY (LeadID|Name|Email|WA|IG|NextAction|LastTouch|Status)
# Order = priority (most likely to close first)
LEADS=(
    "L183|Shudokan|info@shudokan.es|+34661571463|@shudokan.roje|quote_volume_fabric_logo|2026-11-17|AWAITING_REPLY"
    "L132|Alvaro Campeao|pt.alvarocampeao@gmail.com|+351****3601|@alvarotdcampeao|mockup_logo|2026-10-17|AWAITING_LOGO"
    "L026|Brazilian Fight Lisboa|brazilian.fight.lisboa@gmail.com|351910349061|@brazilian.fight.lisboa|quote_quantity_branding|2026-10-20|REPLIED_NEEDS_QUOTE"
    "L3372|TOWASAN Karate Schulen||+498****5508|@towasan_karateschulen|mockup_programme_choice|2026-11-08|WA_REPLIED_NEEDS_MOCKUP"
    "L964|Uzbekistan Kurash Federation|info@ukf.uz|||quote_kurash_bulk|2026-10-22|RFQ_SENT_NO_REPLY"
    "L965|Uzbekistan Kurash Federation (gmail)|ukf.kurash@gmail.com|||quote_kurash_bulk|2026-10-22|RFQ_SENT_NO_REPLY"
)

# Pick lead based on day of month (rotates through all)
DAY=$(date -u '+%d')
IDX=$(( (10#$DAY - 1) % ${#LEADS[@]} ))
LEAD="${LEADS[$IDX]}"

IFS='|' read -r LID NAME EMAIL WA IG ACTION LAST_TOUCH STATUS <<< "$LEAD"

export LID ACTION

echo "🎯 TODAY'S TARGET: $LID - $NAME ($STATUS)" | tee -a "$LOG"
echo "   Last touch: $LAST_TOUCH | Next action: $ACTION" | tee -a "$LOG"

# Create today's closing assets
OUTDIR="/home/ubuntu/closing_campaign_$(date -u '+%Y%m%d')"
mkdir -p "$OUTDIR"

# Generate personalized closing sequence for this lead
case "$LID" in
    L183) # Shudokan - Spain, Judo/Karate/TKD, REPLIED
        cat > "$OUTDIR/email.txt" << 'EOF'
Subject: Shudokan — final nudge before I archive

Hola,

I've sent the catalog, the price list, and asked for your volume/fabric/logo three times now. No reply.

I'll assume the timing isn't right. I'll archive this thread and won't follow up again unless you reach out.

If you do want the quote — just reply with:
1. Units per style (MOQ 30)
2. Fabric: heavy / middle / light
3. Logo file

I'll have the formal quote to you in 24h.

Saludos,
HSN Warrior Apparels
+92 337 333 6381
https://hsnwarriorapparels.vercel.app
EOF
        cat > "$OUTDIR/wa.txt" << 'EOF'
Hola — final nudge. I've asked 3x for volume/fabric/logo to send your quote. No reply = I'll archive.

Still want it? Reply with:
1️⃣ Units/style (min 30)
2️⃣ Fabric: heavy/middle/light
3️⃣ Logo file

Quote in 24h.

— HSN Warrior Apparels
+92 337 333 6381
EOF
        ;;
    L132) # Alvaro Campeao - Portugal/UAE, Boxing/Muay Thai, HOT
        cat > "$OUTDIR/email.txt" << 'EOF'
Subject: Alvaro — mockup ready when you are

Hi Alvaro,

Mockup offer from Oct 17 still stands: EUR 77.40 all-in (MMA shorts + tights + JJ gi, branded, door-to-door).

Just need your logo file (AI/SVG/PDF or high-res PNG) and I'll send the mockup today.

If you've moved on, no worries — just let me know.

Best,
HSN Warrior Apparels
+92 337 333 6381
https://hsnwarriorapparels.vercel.app
EOF
        cat > "$OUTDIR/wa.txt" << 'EOF'
Alvaro — mockup offer still open (EUR 77.40 all-in: MMA shorts + tights + JJ gi, branded, DDP shipping).

Just need your logo file → mockup today.

Let me know either way.

— HSN Warrior Apparels
+92 337 333 6381
EOF
        ;;
    L026) # Brazilian Fight Lisboa - Portugal, BJJ, REPLIED
        cat > "$OUTDIR/email.txt" << 'EOF'
Subject: Brazilian Fight Lisboa — your factory quote

Olá,

You asked for factory prices, quantities, and academy branding (Oct 20). Here's the direct answer:

**Factory prices (door-to-door DDP, MOQ 30/style):**
- BJJ Gi (pearl weave 450gsm): €29.60
- Rank belt: €3.00
- Rash guard (poly/spandex): €11.50
- MMA shorts: €9.90
- Spats/tights: €11.50
- Boxing gloves 12oz (PU): €25.50
- Shin guards: €28.50
- Headgear: €24.00
- Hoodie (branded): €14.50

**Your academy branding:** FREE on all items (logo required)
**Production:** 4–6 weeks from deposit
**Shipping:** DHL/FedEx DDP — customs handled, zero surprise fees

Reply with quantities per style/colour + logo file → formal quote + mockup in 24h.

Abraço,
HSN Warrior Apparels
+92 337 333 6381
https://hsnwarriorapparels.vercel.app
EOF
        cat > "$OUTDIR/wa.txt" << 'EOF'
Olá! You asked for factory prices + academy branding (Oct 20). Direct prices (DDP, MOQ 30):

🥋 BJJ Gi: €29.60
🥋 Belt: €3.00
🥋 Rash guard: €11.50
🥋 MMA shorts: €9.90
🥋 Spats: €11.50
🥊 Gloves 12oz: €25.50
🦵 Shin guards: €28.50
🛡️ Headgear: €24.00
🧥 Hoodie: €14.50

Branding FREE. 4–6 wks production. DHL/FedEx DDP (customs included).

Reply: quantities/style + logo → quote + mockup in 24h.

— HSN Warrior Apparels
+92 337 333 6381
EOF
        ;;
    L3372) # TOWASAN - Germany, Karate, WA REPLIED
        cat > "$OUTDIR/email.txt" << 'EOF'
Subject: TOWASAN — which programme first?

Hi,

You replied on WhatsApp (Nov 7) asking for a class outline and our role. I sent the full product menu with factory prices (gi €29.60, belt €3, gloves €25.50, shin guards €28.50, headgear €24, hoodie €14.50, MOQ 30, 3–4 weeks, DDP).

You have 5 Munich locations, 5 programmes (Lil Dragon 3–5, Kinder 6–8, Jugend 9–13, Erwachsenen 14+, Kickboxen + Morningclass).

**Which programme should we mock up first?** Pick one:
- Lil Dragon dobok (sizes 100–130)
- Kinder/Jugend/Erwachsenen dobok (full size run)
- Kickboxing gear (gloves + shin guards + headgear)
- Walkout hoodies for all 5 locations

Send logo + group sizes for that programme → mockup + formal quote in 24h.

Best,
HSN Warrior Apparels
+92 337 333 6381
https://hsnwarriorapparels.vercel.app
EOF
        cat > "$OUTDIR/wa.txt" << 'EOF'
TOWASAN — which programme first? 🥋

You have 5 Munich locations × 5 programmes. I sent full prices (gi €29.60, belt €3, gloves €25.50, shin guards €28.50, headgear €24, hoodie €14.50, MOQ 30, 3–4 wks, DDP).

Pick ONE to mock up:
1️⃣ Lil Dragon dobok (sizes 100–130)
2️⃣ Kinder/Jugend/Erwachsenen dobok
3️⃣ Kickboxing gear (gloves + shin + headgear)
4️⃣ Walkout hoodies all 5 locations

Send logo + group sizes → mockup + quote in 24h.

— HSN Warrior Apparels
+92 337 333 6381
EOF
        ;;
    L964|L965) # Uzbekistan Kurash Federation - RFQ bulk
        cat > "$OUTDIR/email.txt" << 'EOF'
Subject: Uzbekistan Kurash Federation — kurash uniform bulk quote

Dear Federation,

Following up on my Oct 22 email (RFQ context: kurash uniforms bulk).

We manufacture kurash jackets, belts, and pants to IKA specifications. Factory direct from Sialkot (world's martial arts hub since 1947).

**Bulk pricing (DDP Tashkent, MOQ 100 pcs):**
- Kurash jacket (cotton/poly, IKA cut): €18.50
- Kurash belt (rank colours): €2.80
- Kurash pants (matching fabric): €12.50
- Full set (jacket + belt + pants): €33.80

**Terms:** 50% deposit, 50% pre-ship | 5–7 weeks production | DHL/FedEx DDP (customs included) | Free federation logo on all items

Interested in a formal quote? Reply with:
1. Quantities per size (jacket/pants)
2. Belt rank breakdown
3. Logo file (vector preferred)

Quote + mockup in 24h.

Respectfully,
HSN Warrior Apparels
Mibro International
Sialkot, Pakistan
+92 337 333 6381
hsnwarriorapparel@gmail.com
https://hsnwarriorapparels.vercel.app
EOF
        cat > "$OUTDIR/wa.txt" << 'EOF'
Uzbekistan Kurash Federation — kurash bulk quote follow-up.

IKA-spec kurash sets, factory direct Sialkot:

🥋 Jacket: €18.50
🥋 Belt: €2.80
🥋 Pants: €12.50
🥋 **Full set: €33.80** (DDP Tashkent, MOQ 100)

5–7 wks production. DHL/FedEx DDP (customs included). Free logo.

Want formal quote? Reply:
1. Qty per size (jacket/pants)
2. Belt rank breakdown
3. Logo file

Mockup + quote in 24h.

— HSN Warrior Apparels
+92 337 333 6381
EOF
        ;;
esac

# Also create IG DM version (shorter)
cat > "$OUTDIR/ig_dm.txt" << EOF
Hi $NAME team — following up on our conversation. Quick question: [specific to lead]. Reply here or email/WA and I'll send the formal quote + mockup in 24h. — HSN Warrior Apparels
EOF

echo "📋 Assets created in $OUTDIR:" | tee -a "$LOG"
ls -la "$OUTDIR" | tee -a "$LOG"

# Log the touch in leads.csv (append to Status)
python3 << PYEOF
import csv, datetime, os
lid = os.environ.get('LID', 'L964')
action = os.environ.get('ACTION', 'quote_kurash_bulk')
with open('/home/ubuntu/leads.csv', 'r') as f:
    rows = list(csv.reader(f))
for row in rows:
    if row[0] == lid:
        today = datetime.date.today().isoformat()
        row[11] = row[11] + f" | CLOSING CAMPAIGN TOUCH {today}: {action} (email/WA/IG drafted)"
        break
with open('/home/ubuntu/leads.csv', 'w', newline='') as f:
    csv.writer(f).writerows(rows)
print("✅ Lead status updated")
PYEOF

echo "=== CAMPAIGN COMPLETE ===" | tee -a "$LOG"
exit 0