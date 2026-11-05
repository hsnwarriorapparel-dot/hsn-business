#!/usr/bin/env python3
"""Script-only morning briefing collector (no model calls).

WHY (2026-11-04): the morning-briefing cron was an AGENT job. Its first step
was a script that fetched all the data and wrote /home/ubuntu/morning_briefing.md,
but the job still needed model calls to summarise and deliver it. When the
NVIDIA account was busy, that model call died with HTTP 429 and the whole job
was recorded as FAILED - even though the briefing data had already been
collected successfully. The retry then rebuilt everything from zero.

This script does the whole job with ZERO model calls:
  1. run morning_briefing.py (news, HN, tools, market, pipeline numbers)
  2. sweep Gmail + WhatsApp for BUSINESS client replies (no model needed)
  3. emit ONE plain-text briefing that the cron delivers verbatim

It cannot be rate-limited by the model provider, and re-running it is safe.
"""
import os
import re
import subprocess
import sys
import time

HOME = "/home/ubuntu"
BRIEF_MD = os.path.join(HOME, "morning_briefing.md")
OUT = os.path.join(HOME, "morning_briefing_final.txt")

# Personal contacts - NEVER touch, never list, never open.
PERSONAL = ("sayyam", "shamas", "afzal", "chacho nadeem")


def py():
    import glob
    c = sorted(glob.glob(os.path.join(HOME, ".hermes/tools/python-3*/bin/python3")))
    return c[0] if c else sys.executable


def run(cmd, timeout=600):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           cwd=HOME)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT"
    except Exception as exc:
        return 1, str(exc)


def collect_data():
    rc, out = run([py(), os.path.join(HOME, "morning_briefing.py")], timeout=900)
    print(f"[brief] morning_briefing.py rc={rc}", flush=True)
    if not os.path.exists(BRIEF_MD):
        print(f"[brief] FATAL: {BRIEF_MD} not produced\n{out[-500:]}", flush=True)
        return False
    return True


def gmail_business_replies():
    """Scan Gmail for human replies that are NOT auto-acks/platform mail."""
    replies = []
    try:
        sys.path.insert(0, HOME)
        from cdp_helper import get_tabs, connect, make_cdp, js_eval

        tabs = get_tabs()
        gm = [t for t in tabs if "mail.google" in t.get("url", "") and t.get("type") == "page"]
        if not gm:
            print("[brief] no Gmail tab open - skipping Gmail sweep", flush=True)
            return replies
        ws = connect(gm[0])
        cdp = make_cdp(ws)
        cdp("Page.bringToFront")
        query = ("in:inbox newer_than:2d -from:mailer-daemon -from:postmaster "
                 "-from:noreply -from:(no-reply) -from:(notifications@) "
                 "-from:(google.com) -from:(tradewheel) -from:(go4worldbusiness) "
                 "-from:(facebook) -from:(instagram) -from:(linkedin)")
        js = """(()=>{
          const box=document.querySelector('input[aria-label="Search mail"]') ||
                    document.querySelector('input[name="q"]');
          if(!box) return 'no-box';
          box.focus();
          const setter=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
          setter.call(box,%s);
          box.dispatchEvent(new Event('input',{bubbles:true}));
          for (const type of ['keydown','keypress','keyup']) {
            box.dispatchEvent(new KeyboardEvent(type,{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}));
          }
          return 'typed';
        })()""" % __import__("json").dumps(query)
        js_eval(ws, js, await_promise=False)
        time.sleep(12)
        txt = js_eval(ws, """(()=>{const m=document.querySelector('div[role="main"]');
            return m?m.innerText:'';})()""", await_promise=False) or ""
        ws.close()

        # Auto-acks and out-of-office replies are NOT client replies. They are
        # matched in several languages because the campaign targets DE/NL/PT/ES/
        # IT gyms, and a German auto-ack that slips through reads as a real
        # reply and wastes the user's attention.
        auto_markers = (
            "auto-reply", "auto reply", "automatic reply", "auto-generated",
            "out of office", "mailing list", "unsubscribe", "do not reply",
            "abwesenheitsinformation", "vielen dank f", "vielen dank für ihre",
            "vielen dank für deine", "wir bemühen uns", "bearbeite ich",
            "we will respond", "we'll get back", "thanks for reaching out",
            "thanks for your message", "thanks for your inquiry", "thank you for your",
            "message received", "auto confirmation", "received your message",
            "showing most relevant", "no messages matched", "try using search",
            "conversations", "inbox", "starred", "important", "sent mail",
            "drafts", "spam", "trash", "categories", "labels", "more",
            # bounce / delivery notices, and our own address as sender
            "delivery incomplete", "address not found", "message not delivered",
            "message blocked", "delivery status notification", "undeliverable",
            "hsnwarriorapparel@gmail.com",
        )
        for line in txt.splitlines():
            s = line.strip()
            if not s or len(s) < 6:
                continue
            low = s.lower()
            if any(m in low for m in auto_markers):
                continue
            if any(p in low for p in PERSONAL):
                continue
            if re.search(r"\d+\s*[-–]\s*\d+\s+of\s+[\d,]+", s):
                continue
            # A reply line carries a sender AND something they wrote; Gmail UI
            # chrome (column headers, subject echoes, address fragments) does
            # not. Require a real sender token plus a message body.
            has_sender = ("@" in s) or (":" in s and len(s.split()) >= 3)
            looks_like_header = any(
                s.lower().startswith(h) for h in (
                    "from", "to", "subject", "your message to", "ihre nachricht an",
                    "an:", "von:", "betreff:", "kontakt@", "info@", "mail@",
                ))
            if not has_sender or looks_like_header:
                continue
            if len(s.split()) < 3:
                continue
            replies.append(s[:160])
    except Exception as exc:
        print(f"[brief] Gmail sweep error: {str(exc)[:140]}", flush=True)
    return replies


def whatsapp_business_replies():
    """Scan WhatsApp for BUSINESS client replies (personal contacts excluded).

    Also reports the SESSION state, which is the more important signal: a dead
    WA session (QR login screen) freezes the 10/day WhatsApp quota and the
    user must re-link from their phone. A silent "0 replies" would hide that.

    The WA renderer sometimes wedges: its CDP socket connects but never
    answers. A browser-level Page.reload recovers it, so try that before
    giving up. NEVER open a second WA tab - WhatsApp allows one per profile.
    """
    replies = []
    wa_state = ""
    try:
        sys.path.insert(0, HOME)
        import json as _json
        import urllib.request
        import websocket
        from cdp_helper import get_tabs, connect, js_eval

        tabs = get_tabs()
        wa = [t for t in tabs if "web.whatsapp.com" in t.get("url", "") and t.get("type") == "page"]
        if not wa:
            print("[brief] no WhatsApp tab open - skipping WA sweep", flush=True)
            wa_state = "WhatsApp tab not open - the 10/day WA quota cannot be used."
            return replies, wa_state

        tab = wa[0]
        ws = None
        try:
            # Short timeout: a wedged renderer would otherwise block for the
            # helper's full 60s on every attempt.
            ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=8,
                                             suppress_origin=True)
            js_eval(ws, "(()=>1+1)()", await_promise=False)
        except Exception:
            try:
                if ws is not None:
                    ws.close()
            except Exception:
                pass
            print("[brief] WA renderer wedged - reloading via browser socket", flush=True)
            try:
                ver = _json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/version"))
                bws = websocket.create_connection(ver["webSocketDebuggerUrl"], timeout=15,
                                                 suppress_origin=True)
                bws.send(_json.dumps({"id": 1, "method": "Target.attachToTarget",
                                      "params": {"targetId": tab["id"], "flatten": True}}))
                m = _json.loads(bws.recv())
                sid = m.get("result", {}).get("sessionId")
                if sid:
                    bws.send(_json.dumps({"id": 2, "method": "Page.reload",
                                          "params": {}, "sessionId": sid}))
                    bws.recv()
                bws.close()
            except Exception as exc:
                print(f"[brief] WA reload failed: {str(exc)[:100]}", flush=True)
            time.sleep(6)
            tabs = get_tabs()
            wa = [t for t in tabs if "web.whatsapp.com" in t.get("url", "") and t.get("type") == "page"]
            if not wa:
                print("[brief] WA tab vanished", flush=True)
                wa_state = "WhatsApp tab vanished - the 10/day WA quota cannot be used."
                return replies, wa_state
            tab = wa[0]
            ws = connect(tab)

        body = js_eval(ws, """(()=>document.body?document.body.innerText.slice(0,600):'')()""",
                       await_promise=False) or ""
        pane = js_eval(ws, "(()=>!!document.querySelector('#pane-side'))()", await_promise=False)
        ws.close()

        low = (body or "").lower()
        if "scan to log in" in low or "log in with phone number" in low or not pane:
            wa_state = ("WhatsApp session DEAD (QR login screen) - the 10/day WA quota "
                        "is FROZEN until you re-link from your phone (WhatsApp > linked devices).")
            print("[brief] " + wa_state, flush=True)
            return replies, wa_state

        for line in (body or "").splitlines():
            s = line.strip()
            if not s or len(s) < 4:
                continue
            if any(p in s.lower() for p in PERSONAL):
                continue
            replies.append(s[:160])
    except Exception as exc:
        wa_state = f"WhatsApp sweep failed: {str(exc)[:110]}"
        print("[brief] " + wa_state, flush=True)
    return replies, wa_state


def main():
    if not collect_data():
        print("[brief] briefing data collection failed")
        return 1

    body = open(BRIEF_MD, encoding="utf-8", errors="replace").read()

    gmail = gmail_business_replies()
    wa, wa_state = whatsapp_business_replies()

    lines = [body.rstrip(), "", "=" * 40, "📨 CLIENT REPLIES (business only - DRAFT ONLY, not sent)"]
    if gmail:
        lines.append(f"Gmail ({len(gmail)} candidate):")
        for r in gmail[:6]:
            lines.append("  • " + r)
    else:
        lines.append("Gmail: none found (or no Gmail tab open)")
    if wa:
        lines.append(f"WhatsApp ({len(wa)} candidate):")
        for r in wa[:6]:
            lines.append("  • " + r)
    else:
        lines.append("WhatsApp: no replies")
    if wa_state:
        lines.append("")
        lines.append("🚨 " + wa_state)
    lines.append("")
    lines.append("Personal contacts were excluded automatically.")

    out = "\n".join(lines)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(out)
    print(f"[brief] wrote {OUT} ({len(out)} chars)", flush=True)
    print(out, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
