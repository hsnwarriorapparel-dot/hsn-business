#!/usr/bin/env python3
"""Live verification: USA counts, global ammo, wave status, g4w received inquiries (no nav)."""
import csv, json, re, sys, time
sys.path.insert(0, "/home/ubuntu")
exec(open("/home/ubuntu/cdp_helper.py").read())

ROWS = list(csv.DictReader(open("/home/ubuntu/leads.csv")))
print("TOTAL ROWS:", len(ROWS))

def g(r, k):
    for key in r:
        if key and key.strip().lower() == k.lower():
            return r[key] or ""
    return ""

USA = {"usa", "united states", "us", "u.s.", "united states of america"}
usa_rows = [r for r in ROWS if g(r, "Country").strip().lower() in USA]
usa_emailed = [r for r in usa_rows if "email sent" in g(r, "Status").lower()]
usa_open = [r for r in usa_rows if "email sent" not in g(r, "Status").lower()
             and "excluded" not in g(r, "Status").lower()
             and "failed" not in g(r, "Status").lower()]
print(f"USA total={len(usa_rows)} emailed={len(usa_emailed)} open={len(usa_open)}")

# global ammo: has email, no email-sent marker, not excluded/failed
ammo = []
for r in ROWS:
    s = g(r, "Status").lower()
    e = g(r, "Email").strip().lower()
    if not e or "@" not in e:
        continue
    if "email sent" in s or "excluded" in s or "failed" in s:
        continue
    ammo.append(r)
print("GLOBAL AMMO (email, no marker):", len(ammo))
by_country = {}
for r in ammo:
    c = g(r, "Country").strip() or "?"
    by_country[c] = by_country.get(c, 0) + 1
print("ammo by country:", dict(sorted(by_country.items(), key=lambda x: -x[1])[:12]))

# HOT leads
for r in ROWS:
    s = g(r, "Status").lower()
    if "hot" in s:
        print("HOT:", g(r, "Lead ID"), "|", g(r, "Name"), "|", g(r, "Country"), "|", g(r, "Status")[:110])

# last updated rows
stamped = []
for r in ROWS:
    for k in r:
        if k and "status" in k.lower():
            m = re.search(r"(2026-10-(?:2[6-9]|3[01]))", r[k] or "")
            if m:
                stamped.append((m.group(1), r[k][:100]))
            break
from collections import Counter
print("status date tags:", dict(sorted(Counter(d for d, _ in stamped).items())))

# ---- g4w received inquiries: read CURRENT tab without navigating ----
tab = find_tab(lambda t: "go4worldbusiness.com/member/dashboard" in t.get("url", "").lower())
if tab:
    try:
        ws = connect(tab)
        d = js_eval(ws, r"""(() => {
            const t=(document.body&&document.body.innerText)||'';
            return JSON.stringify({len:t.length, text:t.slice(0,3500), href:location.href});
        })()""")
        dd = json.loads(d) if d else {}
        print("\n=== G4W DASH (current, no nav) ===")
        print("href:", dd.get("href"))
        print(dd.get("text", "")[:3500])
        ws.close()
    except Exception as e:
        print("g4w read err:", e)

# IG message requests
tab2 = find_tab(lambda t: "instagram.com/direct/requests" in t.get("url", ""))
if tab2:
    try:
        ws2 = connect(tab2)
        d2 = js_eval(ws2, r"""(() => { const t=(document.body&&document.body.innerText)||''; return JSON.stringify(t.slice(0,2500)); })()""")
        print("\n=== IG MESSAGE REQUESTS ===")
        print((json.loads(d2) if d2 else "")[:2000])
        ws2.close()
    except Exception as e:
        print("ig req err:", e)
