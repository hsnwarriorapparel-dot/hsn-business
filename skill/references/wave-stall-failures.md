# The 4 Ways a Daily Wave Stalls (2026-11-05) — and the fixes

On 2026-11-05 the Day-22 wave reached **100/100 sent** but only after four
separate stalls. Every one of them failed SILENTLY: the watchdog logged
"runner FAILED to restart" with no reason, and the wave simply stopped
advancing. Check these four whenever a wave stops mid-send.

## 1. Work browser dies (X display loss / D-Bus disconnect / renderer crash)

**Symptom:** wave runner logs `GMAIL NOT READY (no-gmail-tab)` or
`probe-error: <urlopen error [Errno 111] Connection refused>` and pauses.
Every later watchdog tick also fails, because the browser is still dead.

**Cause:** the browser lives on a virtual X display. When that display dies,
Chrome logs `X connection error received` then
`FATAL:dbus/bus.cc:1245] D-Bus connection was disconnected. Aborting.`
and takes the whole browser down.

**Fix (now in `wave_guard.sh`):** before starting a runner, probe
`http://127.0.0.1:9222/json/version`; if it fails, run
`launch_work_browser.sh`, wait, and re-probe. Log "work browser is back up".

**`launch_work_browser.sh` rules (2026-11-05):**
- Pick a LIVE display dynamically (`xdpyinfo -display :21`, then :20). A hardcoded
  display dies with the app that owns it. `:21` is the VNC-backed display
  (x11vnc 5921) and outlives the Hermes Desktop app; `:20` belongs to the
  Desktop's own Xvnc and died on 2026-11-05 21:55, killing the browser with it.
- Launch with `setsid` so an agent session cleanup cannot SIGKILL it.
- Open ALL THREE work tabs at launch (WhatsApp, Instagram, Gmail). A restart
  that comes up with only WhatsApp leaves the wave with no Gmail tab.
- NEVER open a second WhatsApp tab. WA Web allows one active tab per profile;
  the duplicate shows "WhatsApp is open in another window" and must be closed
  via the browser-level `Target.closeTarget`, not by reloading the real tab.

## 2. Stale wave lock

**Symptom:** `wave_guard.sh` exits silently every tick; the log shows
"wave not running; N lead(s) unsent -> restarting runner" followed by
"runner FAILED to restart", and NOTHING is ever sent again.

**Cause:** `dayNN_wave.lock` holds the owner's PID. If the runner is killed
(SIGKILL, OOM, X death) it never removes the lock, and the guard's
`if [ -f "$LOCK" ]; then exit 0` treats garbage as "owned by a live process".

**Fix (now in `wave_guard.sh`):** read the PID out of the lock; if
`kill -0 $PID` fails the owner is dead, so log "stale wave lock ... reclaiming"
and `rm -f` it. Only a LIVE owner blocks a restart.

## 3. Missing Python package (websocket-client)

**Symptom:** "runner FAILED to restart" every tick, and
`wave_guard_runner.log` shows
`ModuleNotFoundError: No module named 'websocket'` from `cdp_helper.py`.
The wave is stuck at exactly the point it died.

**Cause:** the pinned interpreter
`/home/ubuntu/.hermes/tools/python-3.14.7+*/bin/python3` lost its
third-party site-packages (its `site-packages/` had been reduced to just
`pip` + `README.txt`). Note `websocket-client` (singular import `websocket`)
is DIFFERENT from `websockets` (the asyncio library) — the latter can be
installed while the former is missing, which makes this confusing.

**Fix (now in `wave_guard.sh`):** pre-flight `import websocket`; if it fails,
`pip install --no-input websocket-client` with the pinned interpreter and
re-check before starting the runner. The guard also now tails the last 5
lines of `wave_guard_runner.log` into its own log on failure, so the reason
is never hidden again.

**Manual repair:**
```bash
PY=/home/ubuntu/.hermes/tools/python-3.14.7+20260901-linux-arm64/bin/python3
"$PY" -m pip install --no-input --disable-pip-version-check websocket-client
"$PY" -c "import websocket; print(websocket.__version__)"
```

## 4. Quota-trim BEFORE the already-sent filter (wave never advances)

**Symptom:** every run reports the same count, e.g.
`WAVE COMPLETE: 0 sent, 0 failed, 50 skipped`, forever, even though the
CSV says the leads are unsent.

**Cause:** the runner trimmed `ids` to the remaining daily allowance FIRST,
so it kept re-picking the FIRST N wave IDs — which were all already sent —
and never reached the genuinely unsent leads further down the file.

**Fix (in `dayNN_wave_runner.py`):** filter out already-sent leads FIRST,
then trim to the allowance. Log both numbers so the order is visible:
`filtered N already-sent lead(s) from the wave before trimming`.

## Do not run CDP diagnostics DURING a wave

Every browser crash above was made worse by a second CDP client on the same
Gmail tab. A diagnostic that types into the Search-mail input while the wave
is composing mail will kill the renderer. **Rule: during an active wave,
monitor with file reads only** (`tail dayNN_log.txt`, `grep -c` on
`leads.csv`). Run CDP probes only when no runner is alive.

## Verify with the CSV first, Gmail second

`grep -c "email sent (Daily YYYY-MM-DD)" /home/ubuntu/leads.csv` is instant,
local and cannot crash anything. Use it to track wave progress. Use Gmail
only for the final audit, and split the count by subject variant
(`templates.EMAIL_SUBJECTS`) when the result set exceeds 50 — above 50
Gmail returns "1-50 of many" and no exact number.

Note: Gmail's `after:` filter uses the ACCOUNT's timezone, and the campaign
day tag is PKT-based, so `after:2026/11/05` can include the previous
campaign day's late sends. Confirm with a known recipient per window.
