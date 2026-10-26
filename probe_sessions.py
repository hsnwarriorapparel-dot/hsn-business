#!/usr/bin/env python3
"""Probe work-browser sessions: Gmail / WhatsApp / Instagram login state.
Opens one tab per service (none open currently), reports state, closes extras.
NEVER types credentials. Read-only probe.
"""
import sys, time, json, urllib.request
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

CDP_HTTP = "http://127.0.0.1:9222"

def open_tab(url, wait=9):
    ver = json.load(urllib.request.urlopen(f"{CDP_HTTP}/json/version"))
    ws = websocket = None
    import websocket as _w
    ws = _w.create_connection(ver["webSocketDebuggerUrl"], timeout=30, suppress_origin=True)
    cdp = make_cdp(ws)
    cdp("Target.createTarget", {"url": url})
    ws.close()
    time.sleep(wait)
    return get_tabs()

def pages():
    return [t for t in get_tabs() if t.get("type") == "page"]

def probe(tab, expr):
    try:
        ws = connect(tab)
        v = js_eval(ws, expr, await_promise=False)
        ws.close()
        return v
    except Exception as e:
        return f"ERR:{str(e)[:90]}"

def find(sub):
    for t in pages():
        if sub in t.get("url", ""):
            return t
    return None

report = {}

# ---- GMAIL ----
g = find("mail.google")
if not g:
    open_tab("https://mail.google.com/mail/u/0/#inbox", wait=11)
    g = find("mail.google")
if g:
    report["gmail_url"] = g["url"][:80]
    report["gmail_title"] = g.get("title", "")[:60]
    report["gmail_state"] = probe(g, r"""(() => {
      const b = document.body;
      if (!b) return 'no-body';
      const txt = b.innerText || '';
      if (/Sign in|accounts.google.com/i.test(txt) && !/Compose/i.test(txt)) return 'LOGIN-WALL';
      const compose = Array.from(document.querySelectorAll('div[role="button"], .T-I')).find(e => /^Compose$/i.test((e.innerText||'').trim()));
      const dlgs = document.querySelectorAll('div[role="dialog"]').length;
      const stale = Array.from(document.querySelectorAll('div[role="dialog"]')).filter(d => /New Message|Compose/i.test((d.innerText||'').slice(0,30))).length;
      return JSON.stringify({compose: !!compose, dialogs: dlgs, composeDialogs: stale, txt: txt.slice(0,120)});
    })()""")
else:
    report["gmail_state"] = "NO-TAB"

# ---- WHATSAPP ----
w = find("web.whatsapp")
if not w:
    open_tab("https://web.whatsapp.com/", wait=12)
    w = find("web.whatsapp")
if w:
    report["wa_url"] = w["url"][:80]
    report["wa_state"] = probe(w, r"""(() => {
      const t = document.body ? (document.body.innerText || '') : '';
      if (/Scan to log in|Log in to WhatsApp/i.test(t)) return 'QR-SESSION-DEAD';
      if (document.querySelector('#pane-side')) return 'ALIVE #pane-side';
      return 'UNKNOWN:' + t.slice(0,80);
    })()""")
else:
    report["wa_state"] = "NO-TAB"

# ---- INSTAGRAM ----
i = find("instagram.com")
if not i:
    open_tab("https://www.instagram.com/", wait=10)
    i = find("instagram.com")
if i:
    report["ig_url"] = i["url"][:80]
    report["ig_state"] = probe(i, r"""(() => {
      const t = document.body ? (document.body.innerText || '') : '';
      if (/Log in to Instagram|accounts.instagram.com/i.test(t)) return 'LOGIN-WALL';
      if (/Your activity|New post|Search/i.test(t)) return 'ALIVE';
      return 'UNKNOWN:' + t.slice(0,80);
    })()""")
else:
    report["ig_state"] = "NO-TAB"

print(json.dumps(report, indent=2))
