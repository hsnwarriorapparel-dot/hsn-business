# Browser Tab Recovery — WA / go4worldbusiness renderer wedges

Observed 2026-11-05 on the VPS work browser (Chromium snap, CDP 9222).

## Symptom

`connect(tab)` succeeds instantly (the WebSocket handshake completes) but the
first `recv()` never returns — `WebSocketTimeoutException: Connection timed
out`. It affects SPECIFIC tabs (WhatsApp, go4worldbusiness) while Gmail and
Instagram keep working, so it is NOT a dead browser or a CDP-port problem.

Even `Page.getFrameTree` — which does not touch page JavaScript — times out.
The renderer processes sit at ~0% CPU in `futex_do_wait`, so they are BLOCKED,
not spinning. Cause is not fully known; it correlates with long-lived tabs.

## Recovery (works, verified)

Reload the target through the BROWSER-level socket. That channel is never
wedged, because it does not depend on the stuck renderer's message loop:

```python
import json, urllib.request, websocket
ver = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/version"))
ws = websocket.create_connection(ver["webSocketDebuggerUrl"], timeout=20,
                                 suppress_origin=True)
ws.send(json.dumps({"id": 1, "method": "Target.attachToTarget",
                     "params": {"targetId": tab_id, "flatten": True}}))
sid = json.loads(ws.recv())["result"]["sessionId"]
ws.send(json.dumps({"id": 2, "method": "Page.reload", "params": {},
                     "sessionId": sid}))
ws.recv()
ws.close()
```

After the reload the page socket answers normally again.

## Pitfalls

- `cdp_helper.connect()` uses `timeout=60`. On a wedged renderer that means a
  60s stall per attempt. Probe with a SHORT timeout (8s) and reload on failure.
- `Page.captureScreenshot` ALSO hangs on the wedged renderer (it blocks on the
  compositor). To grab an image from a WhatsApp QR canvas, read the bytes out
  of the DOM instead: `canvas.toDataURL('image/png')` works fine.
- NEVER open a second WhatsApp tab to work around a dead one — WhatsApp
  allows ONE web tab per profile, and a second tab shows "WhatsApp is open in
  another window" and can kill the pane. Reload the existing tab.
- After recovering, RE-CHECK the session state: a recovered tab may still be
  on the "Scan to log in" screen (session genuinely dead, needs the user's
  phone) even though the renderer now responds.

## Scripts

- `/home/ubuntu/capture_wa_qr.py` — recovers the WA tab and exports the login
  QR to `/home/ubuntu/wa_qr.png` (canvas toDataURL, not a screenshot).
  Deliver that file with `MEDIA:/home/ubuntu/wa_qr.png` so the user can scan
  it from Telegram instead of needing the VNC screen.

## Reporting the WA session state

A dead WA session freezes the 10/day WhatsApp quota. Report it as a top-line
blocker in the morning briefing, not as "0 replies" — a silent zero hides it.
`morning_briefing_collect.py` now does this and prints:
"WhatsApp session DEAD (QR login screen) - the 10/day WA quota is FROZEN ..."
