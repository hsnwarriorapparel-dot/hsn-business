#!/usr/bin/env python3
"""IG inbox full read + go4WorldBusiness received inquiries (Page.navigate, fresh connection)."""
import json, sys, time
sys.path.insert(0, "/home/ubuntu")
exec(open("/home/ubuntu/cdp_helper.py").read())

# ---------- IG inbox full list ----------
tab = find_tab(lambda t: "instagram.com/direct/inbox" in t.get("url", ""))
if tab:
    try:
        ws = connect(tab)
        d = js_eval(ws, r"""(() => {
            const out=[];
            document.querySelectorAll('[role="listitem"], li, div[dir="auto"]').forEach(()=>{});
            const txt=(document.body&&document.body.innerText)||'';
            return JSON.stringify({len:txt.length, text:txt.slice(0,9000)});
        })()""")
        dd = json.loads(d) if d else {}
        print("=== IG INBOX TEXT (len %s) ===" % dd.get("len"))
        print(dd.get("text","")[:9000])
        ws.close()
    except Exception as e:
        print("ig err:", e)

# ---------- g4w: use Page.navigate (returns immediately) on dashboard tab ----------
tab2 = find_tab(lambda t: "go4worldbusiness.com/member/dashboard" in t.get("url", "").lower())
print("\n=== g4w dash tab:", bool(tab2))
if tab2:
    try:
        ws = connect(tab2)
        cdp = make_cdp(ws)
        for path in ["inquiries", "inquiries-received", "my-inquiries"]:
            try:
                cdp("Page.navigate", {"url": "https://www.go4worldbusiness.com/member/dashboard/%s/" % path})
                time.sleep(7)
                d = js_eval(ws, r"""(() => { const t=(document.body&&document.body.innerText)||''; return JSON.stringify({url:location.href, text:t.slice(0,2500)}); })()""")
                dd = json.loads(d) if d else {}
                print("\n----- g4w %s -> url=%s" % (path, dd.get("url")))
                print(dd.get("text","")[:1800])
            except Exception as e:
                print("g4w path", path, "err", e)
        ws.close()
    except Exception as e:
        print("g4w connect err:", e)
