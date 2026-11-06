#!/usr/bin/env bash
# Launch the HSN work browser (profile work-profile-1) on the BOT SCREEN :20
# with CDP on 9222, fully detached so agent session cleanup never kills it.
#
# WHY DETACHED (2026-11-05): launching Chromium through terminal(background=true)
# got it SIGKILL'd twice when the Hermes session released its child processes.
# setsid + nohup detach it from the agent process group, so it survives.
set -u
PROFILE=/home/ubuntu/work-profile-1
CHROME=/snap/chromium/current/usr/lib/chromium-browser/chrome
LOG=/home/ubuntu/work_browser.log

# already running?
if pgrep -f "user-data-dir=$PROFILE" > /dev/null 2>&1; then
  echo "work browser already running"
  exit 0
fi

# Pick a LIVE virtual display. :20 is the Hermes Desktop's own Xvnc and it
# DIED on 2026-11-05 21:55, which killed the work browser with
# "X connection error received" -> "D-Bus connection was disconnected".
# :21 (started by vps_boot.sh) is the VNC-backed display (x11vnc 5921) and
# survives independently of the Desktop app.
export XAUTHORITY=/home/ubuntu/.hermes/bot-desktop/Xauthority
# PIN the bot screen to :20 (2026-11-05): the auto-pick preferred :21 (the
# user's VNC display) but the user watches :20, so the browser landed on the
# wrong screen and looked "invisible". Use :20 unless it is down.
export DISPLAY=""
for d in :20 :21; do
    if xdpyinfo -display "$d" >/dev/null 2>&1; then
        export DISPLAY="$d"
        break
    fi
done
if [ -z "$DISPLAY" ]; then
    echo "NO LIVE VIRTUAL DISPLAY - cannot launch the work browser"
    exit 1
fi
echo "using DISPLAY=$DISPLAY"
export XDG_RUNTIME_DIR=/home/ubuntu/.hermes/bot-desktop/xdg
export XDG_CONFIG_HOME=/home/ubuntu/.hermes/bot-desktop/xdg/config
export XDG_CACHE_HOME=/home/ubuntu/.hermes/bot-desktop/xdg/cache
export XDG_DATA_HOME=/home/ubuntu/.hermes/bot-desktop/xdg/data

setsid "$CHROME" \
  --user-data-dir="$PROFILE" \
  --remote-debugging-port=9222 \
  --no-first-run --no-default-browser-check \
  --start-maximized \
  --password-store=basic \
  --disable-session-crashed-bubble \
  --disable-gpu --disable-software-rasterizer \
  --disable-features=WebGL \
  --restore-last-session \
  "https://web.whatsapp.com/" \
  "https://www.instagram.com/" \
  "https://mail.google.com/mail/u/0/#inbox" \
  >> "$LOG" 2>&1 < /dev/null &

disown
sleep 8
if pgrep -f "user-data-dir=$PROFILE" > /dev/null 2>&1; then
    echo "work browser launched on $DISPLAY (pid $(pgrep -f "user-data-dir=$PROFILE" | head -1))"
    curl -s -m 5 http://127.0.0.1:9222/json/version | head -2
else
    echo "FAILED to launch - see $LOG"
    tail -20 "$LOG"
    exit 1
fi

# TAB SELF-HEAL (2026-11-05): a browser restart can come up with only SOME of
# the work tabs. The email wave needs a Gmail tab (it stops with
# "GMAIL NOT READY (no-gmail-tab)" without one) and the IG pass needs an
# Instagram tab. Reopen whatever is missing. NEVER open a second WhatsApp
# tab - WhatsApp Web allows only one active tab per profile and a duplicate
# tab shows "open in another window" and breaks the pane.
python3 - "$@" <<'PYEOF' 2>/dev/null || true
import json, sys, time, urllib.request, websocket
sys.path.insert(0, '/home/ubuntu')
try:
    from cdp_helper import get_tabs, make_cdp
except Exception:
    sys.exit(0)

NEEDED = [('gmail', 'https://mail.google.com/mail/u/0/#inbox',
           'mail.google'),
          ('ig', 'https://www.instagram.com/', 'instagram.com')]

try:
    ver = json.load(urllib.request.urlopen('http://127.0.0.1:9222/json/version'))
except Exception:
    sys.exit(0)

for key, url, pat in NEEDED:
    tabs = get_tabs()
    if any(pat in t.get('url', '') and t.get('type') == 'page' for t in tabs):
        continue
    try:
        ws = websocket.create_connection(ver['webSocketDebuggerUrl'], timeout=30,
                                         suppress_origin=True)
        make_cdp(ws)('Target.createTarget', {'url': url})
        ws.close()
        print('reopened missing tab: %s' % key)
        time.sleep(6)
    except Exception:
        pass
PYEOF
