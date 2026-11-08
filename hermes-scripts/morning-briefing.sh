#!/bin/bash
# HSN morning briefing - script-only cron (no model calls).
#
# WHY SCRIPT-ONLY (2026-11-04): this job used to be an agent job. The data
# collection was already a script, but the summary + delivery needed model
# calls. When the NVIDIA account was busy, that model call failed with HTTP 429
# and the whole job was recorded FAILED - even though the briefing had already
# been built - and the retry rebuilt everything from zero.
#
# This script does the whole job with ZERO model calls, so a provider rate
# limit can never fail it. Re-running is safe.
set -u

PY="$(ls -d /home/ubuntu/.hermes/tools/python-3*/bin/python3 2>/dev/null | head -1)"
[ -z "$PY" ] && PY="/usr/bin/python3"

cd /home/ubuntu || exit 1

"$PY" /home/ubuntu/morning_briefing_collect.py
RC=$?

if [ $RC -ne 0 ]; then
    echo "morning briefing FAILED (rc=$RC) - see /home/ubuntu/morning_briefing.log"
    exit $RC
fi

# Deliver the composed briefing verbatim (the cron delivers stdout).
if [ -s /home/ubuntu/morning_briefing_final.txt ]; then
    cat /home/ubuntu/morning_briefing_final.txt
else
    echo "morning briefing produced no output file"
    exit 1
fi
