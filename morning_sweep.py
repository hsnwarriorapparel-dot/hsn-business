#!/usr/bin/env python3
"""Live sweep for HSN morning briefing: WA session state + chat replies, Gmail business replies, IG DM replies."""
import json, re, sys, time
sys.path.insert(0, "/home/ubuntu")
exec(open("/home/ubuntu/cdp_helper.py").read())

OUT = {}

# ---------- 1. WHATSAPP: enumerate ALL WA tabs, never reload ----------
wa_tabs = [t for t in get_tabs() if t.get("type") == "page" and "web.whatsapp.com" in t.get("url", "")]
print(f"WA tabs found: {len(wa_tabs)}", flush=True)
wa_report = []
for t in wa_tabs:
    try:
        ws = connect(t)
        info = js_eval(ws, r"""(() => {
            const t = (document.body && document.body.innerText) || "";
            return JSON.stringify({
                hasQR: /Scan to log in|Log in to WhatsApp/i.test(t),
                hasPane: !!document.querySelector('#pane-side'),
                hasChatList: !!document.querySelector('[aria-label="Chat list"]'),
                title: document.title,
                textHead: t.slice(0, 200)
            });
        })()""")
        d = json.loads(info) if info else {}
        wa_report.append(d)
        print(f"WA tab {t['id'][:8]}: QR={d.get('hasQR')} pane={d.get('hasPane')} chatlist={d.get('hasChatList')}", flush=True)
        ws.close()
    except Exception as e:
        print(f"WA tab {t['id'][:8]} ERR {e}", flush=True)
        wa_report.append({"error": str(e)})

alive = [r for r in wa_report if r.get("hasPane") and not r.get("hasQR")]
OUT["wa_alive"] = bool(alive)
OUT["wa_qr"] = any(r.get("hasQR") for r in wa_report)
OUT["wa_report"] = wa_report

# If WA alive, read recent chat list titles + last messages for business replies
if alive:
    try:
        ws = connect(wa_tabs[0])
        chats = js_eval(ws, r"""(() => {
            const out = [];
            document.querySelectorAll('#pane-side [role="listitem"], [data-tab]').forEach(() => {});
            const rows = document.querySelectorAll('[role="gridcell"], [role="listitem"]');
            rows.forEach(r => {
              const tx = (r.innerText || '').trim();
              if (tx) out.push(tx.replace(/\n+/g, ' | ').slice(0, 200));
            });
            return JSON.stringify(out.slice(0, 40));
        })()""")
        OUT["wa_chats"] = json.loads(chats) if chats else []
        ws.close()
    except Exception as e:
        print("WA chat read err:", e, flush=True)

# ---------- 2. GMAIL: business replies sweep ----------
gmail_tab = find_tab(lambda t: "mail.google.com" in t.get("url", ""))
OUT["gmail_found"] = bool(gmail_tab)
if gmail_tab:
    try:
        ws = connect(gmail_tab)
        js_eval(ws, r"""(() => { location.hash = '#inbox'; return 1; })()""")
        time.sleep(3)
        # search for recent mail
        q = "in:inbox newer_than:3d"
        js_eval(ws, """(() => { location.hash = '#search/' + encodeURIComponent(%s); return 1; })()""" % json.dumps(q))
        time.sleep(5)
        rows = js_eval(ws, r"""(() => {
            const out = [];
            document.querySelectorAll('tr').forEach(tr => {
              const fromEl = tr.querySelector('span[email]');
              const from = fromEl ? fromEl.getAttribute('email') : '';
              const txt = (tr.innerText || '').trim().replace(/\n+/g, ' | ');
              if (txt) out.push({from: from, txt: txt.slice(0, 300)});
            });
            return JSON.stringify(out.slice(0, 60));
        })()""")
        data = json.loads(rows) if rows else []
        # filter: exclude bounces + auto-acks infrastructure senders
        junk_senders = ("mailer-daemon", "postmaster", "noreply", "no-reply", "notifications@", "mail-daemon")
        bounce_markers = ("address not found", "delivery incomplete", "message not delivered",
                          "undeliverable", "returned mail", "delivery status notification", "mail blocked",
                          "message blocked", "does not exist")
        humans, bounces, acks = [], [], []
        for r in data:
            f = (r.get("from") or "").lower()
            tx = (r.get("txt") or "").lower()
            if any(m in tx for m in bounce_markers) or "mailer-daemon" in f or "postmaster" in f:
                bounces.append(r)
                continue
            if f == "hsnwarriorapparel@gmail.com" and any(m in tx for m in ("delivery incomplete", "message blocked", "address not found")):
                bounces.append(r)
                continue
            if any(s in f for s in junk_senders):
                acks.append(r)
                continue
            humans.append(r)
        OUT["gmail_rows"] = len(data)
        OUT["gmail_human"] = humans
        OUT["gmail_bounces"] = len(bounces)
        OUT["gmail_other"] = acks[:12]
        print(f"GMAIL rows={len(data)} humans={len(humans)} bounces={len(bounces)}", flush=True)
        ws.close()
    except Exception as e:
        print("GMAIL err:", e, flush=True)
        OUT["gmail_error"] = str(e)

# ---------- 3. INSTAGRAM: DM replies ----------
ig_tab = find_tab(lambda t: "instagram.com" in t.get("url", "") and ("/direct" in t.get("url", "") or "instagram.com" in t.get("title", "").lower()))
if ig_tab:
    try:
        ws = connect(ig_tab)
        js_eval(ws, r"""(() => { try { location.href = 'https://www.instagram.com/direct/inbox/'; } catch(e){} return 1; })()""")
        time.sleep(6)
        igdata = js_eval(ws, r"""(() => {
            const t = (document.body && document.body.innerText) || '';
            return JSON.stringify({head: t.slice(0, 3000)});
        })()""")
        d = json.loads(igdata) if igdata else {}
        OUT["ig_head"] = d.get("head", "")[:3000]
        ws.close()
    except Exception as e:
        print("IG err:", e, flush=True)
        OUT["ig_error"] = str(e)

with open("/home/ubuntu/morning_sweep.json", "w") as f:
    json.dump(OUT, f, indent=1, ensure_ascii=False)
print("\n=== WROTE /home/ubuntu/morning_sweep.json ===", flush=True)
print("WA_ALIVE:", OUT.get("wa_alive"), "QR:", OUT.get("wa_qr"), flush=True)
