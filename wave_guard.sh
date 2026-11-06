#!/usr/bin/env bash
# wave_guard.sh — system-crontab watchdog for the daily email wave.
#
# WHY (2026-10-31): the 2026-10-30 overnight wave died at 80/100 because its
# Hermes cron session ended and killed the detached child. The wave runner is
# resumable (it skips any lead already marked 'email sent'), so the watchdog
# simply restarts it if it is not running AND the wave file still has unsent
# leads. It never double-sends: the runner checks the Status column first.
#
# Runs every 10 min from the system crontab (survives Hermes session ends).
set -u
PY="$(ls -d /home/ubuntu/.hermes/tools/python-3*/bin/python3 2>/dev/null | head -1)"
[ -z "$PY" ] && PY="/home/ubuntu/.hermes/tools/python-3.14.7+20260901-linux-arm64/bin/python3"
LOG=/home/ubuntu/wave_guard.log
# Auto-detect the CURRENT day's wave + runner so this watchdog never has to be
# hand-edited each night (it used to hardcode day16 and silently stopped
# guarding the next day's wave). Preference order:
#   1. explicit argument:  wave_guard.sh /path/to/wave.txt
#   2. newest dayNN_wave.txt on disk
#   3. newest dayNN_wave_runner.py next to it
WAVE="${1:-}"
if [ -z "$WAVE" ]; then
  WAVE="$(ls -1t /home/ubuntu/day*_wave.txt 2>/dev/null | head -1)"
fi
[ -z "$WAVE" ] && exit 0
[ -f "$WAVE" ] || exit 0
WAVE_BASE="$(basename "$WAVE")"
# dayNN_wave.txt -> dayNN_wave_runner.py
RUNNER="/home/ubuntu/$(echo "$WAVE_BASE" | sed -E 's/_wave\.txt$/_wave_runner.py/')"
if [ ! -f "$RUNNER" ]; then
  RUNNER="$(ls -1t /home/ubuntu/day*_wave_runner.py 2>/dev/null | head -1)"
fi
[ -z "$RUNNER" ] && exit 0
[ -f "$RUNNER" ] || exit 0
RUNNER_NAME="$(basename "$RUNNER")"
TAG="Daily $(date -u +%Y-%m-%d)"

ts() { date -u '+%Y-%m-%d %H:%M:%S'; }
log() { echo "$(ts) $*" >> "$LOG"; }

# If a post-wave pipeline holds the lock, it owns the wave - do NOT start a
# competing runner (two runners race on one Gmail tab + one leads.csv).
#
# STALE LOCK RECOVERY (2026-11-05): the lock holds the owner's PID. When that
# PID is gone the lock is garbage, and treating it as "held" stalled the wave
# forever - the runner died at 45/50, released nothing, and every watchdog
# tick exited early on the stale lock, so the last 5 leads were never sent.
# Reclaim the lock only when its owner is provably dead.
LOCK="/home/ubuntu/$(echo "$WAVE_BASE" | sed -E 's/_wave\.txt$/_wave\.lock/')"
if [ -f "$LOCK" ]; then
    LOCK_PID="$(cat "$LOCK" 2>/dev/null | tr -dc '0-9')"
    if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
        exit 0            # owner alive -> it owns the wave
    fi
    log "stale wave lock (pid ${LOCK_PID:-unknown} gone) - reclaiming"
    rm -f "$LOCK"
fi

# Is a wave runner already active?
if pgrep -f "$RUNNER_NAME" >/dev/null 2>&1; then
    exit 0
fi

# BROWSER SELF-HEAL (2026-11-05): the wave sends through the work browser's
# CDP port. When that browser dies (X display loss, D-Bus disconnect, renderer
# crash), every runner stops with "GMAIL NOT READY (no-gmail-tab)" and the
# wave stalls forever - exactly what happened on 2026-11-05 (8 sends, then a
# dead browser, then 12 failed watchdog restarts in a row). Relaunch it
# BEFORE starting a runner, and give it time to open the Gmail tab.
if ! curl -s --max-time 5 http://127.0.0.1:9222/json/version >/dev/null 2>&1; then
    log "work browser (CDP 9222) is DOWN - relaunching before the wave"
    bash /home/ubuntu/launch_work_browser.sh >> /home/ubuntu/wave_guard.log 2>&1
    sleep 12
    if ! curl -s --max-time 5 http://127.0.0.1:9222/json/version >/dev/null 2>&1; then
        log "browser relaunch FAILED - skipping this pass (will retry next tick)"
        exit 0
    fi
    log "work browser is back up"
fi

[ -f "$WAVE" ] || exit 0

# Count leads in the wave that are NOT yet marked sent.
UNSENT="$("$PY" - "$WAVE" <<'PYEOF' 2>/dev/null
import csv, sys
wave = [l.strip() for l in open(sys.argv[1]) if l.strip()]
rows = {}
with open('/home/ubuntu/leads.csv', encoding='utf-8-sig', errors='replace') as f:
    for r in csv.DictReader(f):
        for k in r:
            if k and k.strip().lower() == 'lead id':
                rows[r[k].strip()] = r
                break
n = 0
for lid in wave:
    r = rows.get(lid)
    if not r:
        continue
    st = ''
    for k in r:
        if k and k.strip().lower() == 'status':
            st = (r[k] or '').lower()
            break
    # Only restart for genuinely PENDING leads. A lead that already FAILED
    # (dead address), was EXCLUDED by QA, or needs a re-hunt must NOT be
    # retried forever — those are terminal states.
    if 'email sent' in st:
        continue
    if 'email failed' in st or 'failed' in st or 'excluded' in st or 're-hunt' in st:
        continue
    n += 1
print(n)
PYEOF
)"
[ -z "${UNSENT:-}" ] && exit 0
[ "$UNSENT" -gt 0 ] 2>/dev/null || exit 0

log "wave not running; $UNSENT lead(s) unsent in $WAVE -> restarting runner"
cd /home/ubuntu || exit 1

# PRE-FLIGHT IMPORT CHECK (2026-11-05): the runner imports websocket-client
# via cdp_helper. If that package goes missing, the runner dies instantly with
# ModuleNotFoundError and every watchdog tick logs "runner FAILED to restart"
# without saying WHY - the wave then stalls for hours. Verify the import
# BEFORE starting, and repair it (pip install) if it is gone.
if ! "$PY" -c "import websocket" >/dev/null 2>&1; then
    log "websocket-client missing from $PY - reinstalling"
    "$PY" -m pip install --no-input --disable-pip-version-check websocket-client >> "$LOG" 2>&1
    if ! "$PY" -c "import websocket" >/dev/null 2>&1; then
        log "websocket-client reinstall FAILED - skipping this pass"
        exit 0
    fi
    log "websocket-client restored"
fi

setsid nohup "$PY" "$RUNNER" --wave "$WAVE" --day "$TAG" >> /home/ubuntu/wave_guard_runner.log 2>&1 < /dev/null &
sleep 8
if pgrep -f "$RUNNER_NAME" >/dev/null 2>&1; then
  log "runner restarted OK"
else
  log "runner FAILED to restart - last lines:"
  tail -5 /home/ubuntu/wave_guard_runner.log >> "$LOG"
fi
