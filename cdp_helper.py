#!/usr/bin/env python3
"""CDP helper for driving the work-profile Chromium (Instagram/WhatsApp/Gmail logged in).
Usage: import from other scripts via exec(open(...).read()) or run standalone smoke test."""
import json, urllib.request, websocket, time, sys

CDP_HTTP = "http://127.0.0.1:9222"

def get_tabs():
    return json.load(urllib.request.urlopen(f"{CDP_HTTP}/json"))

def find_tab(predicate):
    for t in get_tabs():
        if t["type"] == "page" and predicate(t):
            return t
    return None

def connect(tab):
    ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=60,
                                     suppress_origin=True)
    return ws

def make_cdp(ws):
    _id = [0]
    def cdp(method, params=None):
        _id[0] += 1
        ws.send(json.dumps({"id": _id[0], "method": method, "params": params or {}}))
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == _id[0]:
                if "error" in msg:
                    raise RuntimeError(f"CDP error: {msg['error']}")
                return msg.get("result", {})
    return cdp

def js_eval(ws, expr, await_promise=True):
    cdp = make_cdp(ws)
    return cdp("Runtime.evaluate", {
        "expression": expr,
        "returnByValue": True,
        "awaitPromise": await_promise,
        "userGesture": True,
    })["result"].get("value")

def open_new_tab(url):
    """Uses the browser-level endpoint to open a new tab."""
    ws = websocket.create_connection(
        json.load(urllib.request.urlopen(f"{CDP_HTTP}/json/list"))[0]["webSocketDebuggerUrl"].replace("page", "browser") if False else
        get_tabs()[0]["webSocketDebuggerUrl"],
        timeout=30, suppress_origin=True)
    # find browser-level ws url
    import urllib.parse
    ver = json.load(urllib.request.urlopen(f"{CDP_HTTP}/json/version"))
    ws2 = websocket.create_connection(ver["webSocketDebuggerUrl"], timeout=30, suppress_origin=True)
    cdp = make_cdp(ws2)
    cdp("Target.createTarget", {"url": url})
    ws.close(); ws2.close()
    import time as _t; _t.sleep(4)

def navigate(tab_url_pattern, new_url):
    """Find a page matching pattern and navigate it; returns the tab."""
    t = find_tab(lambda x: tab_url_pattern in x["url"])
    if not t:
        return None
    ws = connect(t)
    cdp = make_cdp(ws)
    cdp("Page.enable")
    cdp("Page.navigate", {"url": new_url})
    time.sleep(4)
    return t

if __name__ == "__main__":
    tabs = get_tabs()
    for t in tabs:
        if t["type"] == "page":
            print(t["title"][:60], "|", t["url"][:80])
