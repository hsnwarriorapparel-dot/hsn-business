#!/usr/bin/env python3
"""Classify Gmail sweep hits into REAL client replies vs auto-replies vs noise.
Read-only. Prints only real inbound client replies for the cron report."""
import sys, time, json, re
from urllib.parse import quote
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

PERSONAL = re.compile(r'sayyam|shamas|afzal|chacho', re.I)
AUTOMAIL = re.compile(r'mailer-daemon|postmaster|mail-daemon|noreply|no-reply|'
                      r'notifications@google|donotreply|@appointlet', re.I)
AUTO_REPLY = re.compile(r'automatic reply|autoreply|auto-reply|thank you for your email|'
                        r'thanks for reaching out|we will respond|we have received|'
                        r'vielen dank|ich habe diese|sehr geehrte', re.I)
SELF = re.compile(r'^me$|^hsnwarriorapparel@gmail\.com$', re.I)

JS = r"""(() => {
  const spans = Array.from(document.querySelectorAll('span[email]'));
  const seen = new Set(); const out = [];
  for (const s of spans) {
    const from = s.getAttribute('email') || '';
    if (!from || seen.has(from)) continue;
    seen.add(from);
    let row = s.closest('div[role="listitem"]') || s.closest('div.adn.ads') ||
              s.closest('tr') || s.closest('div');
    const txt = row ? (row.innerText || '').replace(/\s+/g, ' ').trim() : '';
    out.push({from: from, snippet: txt.slice(0, 260)});
  }
  return JSON.stringify({items: out});
})()"""

tabs = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
if not tabs:
    print(json.dumps({"error": "no gmail tab"})); sys.exit(1)
tab = tabs[0]
ws = connect(tab)
cdp = make_cdp(ws)
cdp("Page.enable")
cdp("Page.bringToFront")

cdp("Page.navigate", {"url": "https://mail.google.com/mail/u/0/#search/" +
                       quote("newer_than:7d -from:me -from:mailer-daemon@google.com")})
time.sleep(9)
v = js_eval(ws, JS, await_promise=False)
try:
    items = json.loads(v).get("items", [])
except Exception:
    items = []

real, autos, noise = [], [], []
for it in items:
    frm = it["from"]
    sn = it["snippet"]
    if PERSONAL.search(frm):
        noise.append((frm, "personal-contact"))
        continue
    if AUTOMAIL.search(frm):
        noise.append((frm, "automated"))
        continue
    if SELF.search(frm):
        noise.append((frm, "our-own-thread"))
        continue
    # our own outbound message: the thread shows "To: <recipient>" as the sender
    # span, and the body is our template
    if re.match(r'^\s*To:\s', sn) or 'HSN Warrior Apparels — martial arts' in sn \
            or 'We noticed your' in sn or 'were asking if' in sn:
        noise.append((frm, "our-outbound-message"))
        continue
    if AUTO_REPLY.search(sn):
        autos.append((frm, sn[:150]))
        continue
    real.append({"from": frm, "snippet": sn[:260]})

print("=== REAL INBOUND CLIENT REPLIES ===")
print(json.dumps(real, indent=2, ensure_ascii=False))
print(f"\n=== auto-replies (no action): {len(autos)} ===")
for a in autos[:12]:
    print("  ", a[0], "|", a[1][:110])
print(f"\n=== noise/filtered: {len(noise)} ===")
from collections import Counter
print(dict(Counter(n[1] for n in noise)))
ws.close()
