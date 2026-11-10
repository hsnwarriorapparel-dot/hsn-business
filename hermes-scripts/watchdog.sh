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
  _wd_check=$(mktemp)
  cat > "$_wd_check" <<'PYEOF'
import json, os, datetime
try:
    d = json.load(open('/home/ubuntu/pipeline_completed.json'))
    done = datetime.datetime.strptime(d.get('date'), '%Y-%m-%d').date()
    today = datetime.datetime.now(datetime.timezone.utc).date()
    age = (today - done).days
    if age >= 1:
        print('PIPELINE INCOMPLETE - last completed %s (%d days ago)' % (d.get('date'), age))
except Exception:
    pass
PYEOF
  "$PY" "$_wd_check" 2>/dev/null
  rm -f "$_wd_check"
fi

if ! pgrep -f "/home/ubuntu/.hermes/tools/python-3.14.7+202****0901-linux-arm64/bin/python3 /home/ubuntu/worker.py" > /dev/null; then
    if [ -f /home/ubuntu/worker_restart.lock ]; then
        exit 0
    fi
    cd /home/ubuntu && { /home/ubuntu/.hermes/tools/python-3.14.7+202****0901-linux-arm64/bin/python3 /home/ubuntu/worker.py >> worker_stdout.txt 2>&1 & }
fi

# BROWSER STACK RESTART
#
# A gateway restart kills the Xvnc display and the Chromium work browser
# together, and NOTHING brought them back - so the WhatsApp, Instagram,
# Gmail and go4WorldBusiness channels went dark until someone noticed.
#
# It bit twice on 2026-11-10. The second time a screen_buyers.py job was
# stuck in a retry loop against the dead CDP endpoint, holding the whole
# go4WorldBusiness funnel for 30+ minutes.
#
# Restore in this order: the X server, then the window manager, then the
# browser. launch_work_browser.sh picks a LIVE display itself and refuses
# to start without one, so the display must come first.
if ! curl -s -m 6 http://127.0.0.1:9222/json/version >/dev/null 2>&1; then
    if ! xdpyinfo -display :21 >/dev/null 2>&1; then
        (DISPLAY=:21 nohup Xvnc :21 -geometry 1920x1080 -depth 24           -rfbport 5922 -localhost no -rfbauth /home/ubuntu/.vncpassfile           > /tmp/xvnc.log 2>&1 &)
        sleep 4
    fi
    if xdpyinfo -display :21 >/dev/null 2>&1; then
        (DISPLAY=:21 nohup xfwm4 --display=:21 --replace --compositor=off           > /tmp/xfwm4.log 2>&1 &)
        sleep 1
    fi
    bash /home/ubuntu/launch_work_browser.sh >>/home/ubuntu/work_browser.log 2>&1
    sleep 4
    if curl -s -m 6 http://127.0.0.1:9222/json/version >/dev/null 2>&1; then
        echo "BROWSER RESTARTED (cdp 9222 is back)"
    else
        echo "BROWSER STILL DOWN - CDP 9222 is not answering"
    fi
fi

# NOVNC (port 6080) - Hermes desktop UI access from phone
#
# noVNC proxies the Xvnc display :21 (RFB 5922) to HTTP 6080.
# If it dies, phone can't access Hermes desktop UI.
if ! curl -s -m 6 http://127.0.0.1:6080/ >/dev/null 2>&1; then
    echo "NOVNC DOWN - restarting on 6080"
    pkill -f "websockify.*6080" 2>/dev/null
    sleep 1
    (cd /home/ubuntu && nohup websockify --web /usr/share/novnc/ 6080 localhost:5922 > /tmp/novnc.log 2>&1 &)
    sleep 3
    if curl -s -m 6 http://127.0.0.1:6080/ >/dev/null 2>&1; then
        echo "NOVNC RESTARTED"
    else
        echo "NOVNC STILL DOWN"
    fi
fi

# HERMES DESKTOP IN VNC - ensure it's running on display :21
#
# The Hermes desktop app runs inside the VNC session.
if ! pgrep -f "hermes.*desktop" | grep -v grep > /dev/null; then
    echo "HERMES DESKTOP DOWN - restarting on DISPLAY=:21"
    (DISPLAY=:21 nohup hermes desktop > /tmp/hermes-desktop.log 2>&1 &)
    sleep 5
    if pgrep -f "hermes.*desktop" | grep -v grep > /dev/null; then
        echo "HERMES DESKTOP RESTARTED"
    else
        echo "HERMES DESKTOP STILL DOWN"
    fi
fi

# HERMES DASHBOARD (port 9119) - serves the office-3d plugin
#
# The dashboard serves the NEW 3D office plugin at /office.
if ! curl -s -m 6 http://127.0.0.1:9119/ >/dev/null 2>&1; then
    echo "HERMES DASHBOARD DOWN - restarting on 9119"
    pkill -f "hermes dashboard" 2>/dev/null
    sleep 1
    (cd /home/ubuntu && nohup hermes dashboard --port 9119 > /tmp/hermes-dashboard.log 2>&1 &)
    sleep 8
    if curl -s -m 6 http://127.0.0.1:9119/ >/dev/null 2>&1; then
        echo "HERMES DASHBOARD RESTARTED"
    else
        echo "HERMES DASHBOARD STILL DOWN"
    fi
fi

