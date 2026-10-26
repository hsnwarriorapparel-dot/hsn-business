#!/usr/bin/env python3
"""Client-reply sweep — READ ONLY. Never sends.
Scans Gmail for inbound replies (not from 'me') in the last 2 days, and WhatsApp
for unread chat badges if the session is alive. Excludes personal contacts.
Returns a structured report for the cron message (draft-only)."""
import sys, time, json, re
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

PERSONAL = ['sayyam', 'shamas', 'afzal', 'chacho nadeem', 'chacho nadeem']
report = {"gmail": [], "wa": {}, "errors": []}

# ---------- Gmail ----------
tabs = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
if not tabs:
    report["errors"].append("no gmail tab")
else:
    tab = tabs[0]
    ws = connect(tab)
    cdp = make_cdp(ws)
    cdp("Page.enable")
    cdp("Page.bringToFront")
    cdp("Page.navigate", {"url": "https://mail.google.com/mail/u/0/#search/newer_than:2d+-from:me+(-from:mailer-daemon@google.com)"})
    time.sleep(8)
    v = js_eval(ws, r"""(() => {
      const out = [];
      const rows = Array.from(document.querySelectorAll('div[role="main"] div[role="listitem"]'));
      for (const r of rows) {
        const t = (r.innerText || '').replace(/\s+/g, ' ').trim();
        if (!t) continue;
        const from = (r.querySelector('span[email]') || {}).email || '';
        const subj = (r.querySelector('span[data-thread-subject]') || {}).innerText || '';
        const snippet = t.slice(0, 260);
        if (/mailer-daemon|postmaster|mail-daemon|no-reply|notifications@google/i.test(from + ' ' + subj)) continue;
        if (/^me\b/i.test(t) && /Delivery incomplete|Address not found|failed/i.test(t)) continue;
        out.push({from: from, subject: subj.slice(0, 120), snippet: snippet});
      }
      return JSON.stringify({n: rows.length, items: out.slice(0, 25)});
    })()""", await_promise=False)
    try:
        data = json.loads(v)
    except Exception:
        data = {"n": 0, "items": []}
    report["gmail"] = data.get("items", [])
    report["gmail_total_rows"] = data.get("n", 0)
    ws.close()

# ---------- WhatsApp ----------
wtabs = [t for t in get_tabs() if 'web.whatsapp' in t['url'] and t['type'] == 'page']
if not wtabs:
    report["wa"] = {"state": "no-wa-tab"}
else:
    ws = connect(wtabs[0])
    v = js_eval(ws, r"""(() => {
      const body = document.body ? document.body.innerText : '';
      if (/Scan to log in|Log in to WhatsApp/i.test(body)) return JSON.stringify({state: 'QR-SESSION-DEAD'});
      const badges = Array.from(document.querySelectorAll('span[aria-label]'))
        .filter(s => /unread/i.test(s.getAttribute('aria-label')||''))
        .map(s => ({label: s.getAttribute('aria-label'), title: s.getAttribute('title')||''}));
      return JSON.stringify({state: 'alive', unread: badges.slice(0, 20)});
    })()""", await_promise=False)
    try:
        report["wa"] = json.loads(v)
    except Exception:
        report["wa"] = {"state": "probe-failed"}
    ws.close()

print(json.dumps(report, indent=2, ensure_ascii=False))
