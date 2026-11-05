#!/usr/bin/env python3
"""Recover the WhatsApp tab and capture its login QR code.

The WA renderer wedges: its WebSocket accepts connections but never answers
(even Page.getFrameTree times out), so any CDP call to the page hangs. The
fix is a browser-level Page.reload (the browser socket still works), which
recovers the renderer. Then the QR canvas can be located and screenshotted.

WhatsApp allows ONE web tab per profile - this never opens a second one.
"""
import base64
import json
import os
import sys
import time
import urllib.request
import websocket

sys.path.insert(0, "/home/ubuntu")
from cdp_helper import get_tabs, connect, js_eval, make_cdp

OUT = "/home/ubuntu/wa_qr.png"
CDP_HTTP = "http://127.0.0.1:9222"


def browser_reload(target_id):
    """Reload a target through the BROWSER-level socket (page socket is wedged)."""
    ver = json.load(urllib.request.urlopen(f"{CDP_HTTP}/json/version"))
    ws = websocket.create_connection(ver["webSocketDebuggerUrl"], timeout=20,
                                     suppress_origin=True)
    _id = [0]

    def call(method, params=None, session=None):
        _id[0] += 1
        msg = {"id": _id[0], "method": method, "params": params or {}}
        if session:
            msg["sessionId"] = session
        ws.send(json.dumps(msg))
        while True:
            m = json.loads(ws.recv())
            if m.get("id") == _id[0]:
                return m

    r = call("Target.attachToTarget", {"targetId": target_id, "flatten": True})
    sid = r.get("result", {}).get("sessionId")
    if not sid:
        print("attach failed:", json.dumps(r)[:200])
        ws.close()
        return False
    rr = call("Page.reload", {}, session=sid)
    print("browser-level reload ->", "ok" if "result" in rr else json.dumps(rr)[:160])
    ws.close()
    return True


def main():
    wa = [t for t in get_tabs()
          if t.get("type") == "page" and "web.whatsapp.com" in t.get("url", "")]
    if not wa:
        print("NO_WA_TAB")
        return 1
    tab = wa[0]

    # The page socket may be wedged. Probe it with a SHORT timeout (the
    # helper's default 60s is far too long for a wedged renderer), and
    # reload via the browser socket when it does not answer.
    ws = None
    try:
        ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=8,
                                         suppress_origin=True)
        js_eval(ws, "(()=>1+1)()", await_promise=False)
        print("WA page socket responsive")
    except Exception as exc:
        print(f"WA page socket wedged ({type(exc).__name__}) - reloading via browser socket")
        try:
            if ws is not None:
                ws.close()
        except Exception:
            pass
        browser_reload(tab["id"])
        time.sleep(6)
        wa = [t for t in get_tabs()
              if t.get("type") == "page" and "web.whatsapp.com" in t.get("url", "")]
        if not wa:
            print("WA tab vanished after reload")
            return 1
        tab = wa[0]
        ws = connect(tab)

    cdp = make_cdp(ws)
    cdp("Page.enable")

    probe = (
        "(()=>{"
        "const out=[];"
        "for (const sel of ['canvas','img']) {"
        "  for (const e of document.querySelectorAll(sel)) {"
        "    const r=e.getBoundingClientRect();"
        "    if (r.width>80 && r.height>80 && r.width<700 && r.height<700) {"
        "      out.push({sel:sel,x:Math.round(r.x),y:Math.round(r.y),"
        "               w:Math.round(r.width),h:Math.round(r.height)});"
        "    }"
        "  }"
        "}"
        "return JSON.stringify({vw:innerWidth,vh:innerHeight,cands:out.slice(0,10),"
        "                       body:(document.body?document.body.innerText.slice(0,120):'')});"
        "})()"
    )
    raw = js_eval(ws, probe, await_promise=False)
    info = json.loads(raw or "{}")
    print("viewport:", info.get("vw"), "x", info.get("vh"))
    print("body:", repr(info.get("body", "")[:100]))

    cands = info.get("cands") or []
    if not cands:
        print("NO_QR_ELEMENT - page may not be the login screen")
        ws.close()
        return 1

    best = None
    for c in cands:
        ratio = abs(c["w"] - c["h"]) / max(c["w"], c["h"], 1)
        if ratio > 0.25:
            continue
        score = c["x"] + c["y"]
        if best is None or score < best[0]:
            best = (score, c)
    c = (best or (0, cands[0]))[1]
    print("chosen:", c)

    pad = 16
    x = max(0, c["x"] - pad)
    y = max(0, c["y"] - pad)
    clip = {
        "x": x, "y": y,
        "width": min(info.get("vw", 1920) - x, c["w"] + pad * 2),
        "height": min(info.get("vh", 1080) - y, c["h"] + pad * 2),
        "scale": 2,
    }

    # Page.captureScreenshot hangs on this renderer (it blocks on the
    # compositor for the wedged tab), so pull the QR image bytes directly
    # out of the DOM first: WhatsApp renders it on a <canvas>.
    raw_qr = js_eval(ws, """(()=>{
      const cvs=[...document.querySelectorAll('canvas')].filter(e=>{
        const r=e.getBoundingClientRect();
        return r.width>80 && r.height>80 && r.width<700 && r.height<700;
      });
      if (!cvs.length) return '';
      cvs.sort((a,b)=>{const ra=a.getBoundingClientRect(),rb=b.getBoundingClientRect();
        return (ra.x+ra.y)-(rb.x+rb.y);});
      try { return cvs[0].toDataURL('image/png'); } catch(e) { return ''; }
    })()""", await_promise=False)
    if raw_qr and raw_qr.startswith("data:image/png;base64,"):
        b64 = raw_qr.split(",", 1)[1]
        with open(OUT, "wb") as fh:
            fh.write(base64.b64decode(b64))
        print(f"WROTE {OUT} ({os.path.getsize(OUT)} bytes) [canvas toDataURL]")
        ws.close()
        return 0

    print("canvas toDataURL unavailable - falling back to screenshot")
    shot = cdp("Page.captureScreenshot", {"format": "png", "clip": clip})
    data = shot.get("data")
    if not data:
        print("SCREENSHOT_FAILED")
        ws.close()
        return 1
    with open(OUT, "wb") as fh:
        fh.write(base64.b64decode(data))
    print(f"WROTE {OUT} ({os.path.getsize(OUT)} bytes) [screenshot]")
    ws.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
