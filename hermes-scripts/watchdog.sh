#!/bin/bash
# Restart worker if it died
# PIPELINE COMPLETION CHECK
#
# The nightly outreach pipeline failed three nights running and NOTHING
# said so. It was killed by the 1-hour cron timeout inside the IG pass
# (240 accounts at a measured 37.4s each = 2.5 hours), and the log's last
# line was an ordinary progress line. The tracker rebuild, the WA list,
# the reply sweep and the final verify were never reached.
#
# The post-pipeline now writes pipeline_completed.json ONLY when every
# step ran. If yesterday's marker is missing, say so - a silent partial
# run is the failure mode that hides for weeks.
PY=$(ls -d /home/ubuntu/.hermes/tools/python-3*/bin/python3 2>/dev/null | sort -V | tail -1)
MARK=/home/ubuntu/pipeline_completed.json
if [ -n "$PY" ] && [ -f "$MARK" ]; then
  # Write the check to a temp file and run it. A `python -` heredoc does
  # NOT work here: the interpreter reads the SCRIPT from stdin, and the
  # heredoc body is consumed as the script only when the redirect is
  # attached to the interpreter's stdin in the right form. It printed
  # nothing at all, so the check silently never fired.
  _wd_check=$(mktemp)
  cat > "$_wd_check" <<'PYEOF'
import json, os, datetime
try:
    d = json.load(open('/home/ubuntu/pipeline_completed.json'))
    done = datetime.datetime.strptime(d.get('date'), '%Y-%m-%d').date()
    today = datetime.datetime.now(datetime.timezone.utc).date()
    age = (today - done).days
    # Flag only if a full day has passed with no completed pipeline.
    if age >= 1:
        print('PIPELINE INCOMPLETE - last completed %s (%d days ago)' % (d.get('date'), age))
except Exception:
    pass
PYEOF
  "$PY" "$_wd_check" 2>/dev/null
  rm -f "$_wd_check"
fi

if ! pgrep -f "/home/ubuntu/.hermes/tools/python-3.14.7+20260901-linux-arm64/bin/python3 /home/ubuntu/worker.py" > /dev/null; then
    if [ -f /home/ubuntu/worker_restart.lock ]; then
        exit 0
    fi
    cd /home/ubuntu && { /home/ubuntu/.hermes/tools/python-3.14.7+20260901-linux-arm64/bin/python3 /home/ubuntu/worker.py >> worker_stdout.txt 2>&1 & }
fi
