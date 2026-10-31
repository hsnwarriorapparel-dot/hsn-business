#!/usr/bin/env python3
"""Check go4WorldBusiness dashboard: received inquiries + product count. Read-only."""
import json, sys, time
sys.path.insert(0, "/home/ubuntu")
exec(open("/home/ubuntu/cdp_helper.py").read())

tab = find_tab(lambda t: "go4worldbusiness.com/member/dashboard" in t.get("url", "").lower())
print("dash tab:", bool(tab), flush=True)
if not tab:
    tab = find_tab(lambda t: "go4worldbusiness.com" in t.get("url", "").lower())
if tab:
    ws = connect(tab)
    js_eval(ws, r"""(() => { try { location.href='https://www.go4worldbusiness.com/member/dashboard/'; } catch(e){} return 1; })()""")
    time.sleep(8)
    d = js_eval(ws, r"""(() => {
        const t=(document.body&&document.body.innerText)||'';
        return JSON.stringify({len:t.length, text:t.slice(0,4000)});
    })()""")
    dd = json.loads(d) if d else {}
    print("=== DASHBOARD TEXT ===")
    print(dd.get("text","")[:4000], flush=True)
    # try inquiries pages
    for path in ["inquiries/received", "inquiries", "my-inquiries", "messages"]:
        try:
            js_eval(ws, "(() => { try{location.href='https://www.go4worldbusiness.com/member/dashboard/%s';}catch(e){} return 1;})()" % path)
            time.sleep(6)
            dd2 = js_eval(ws, r"""(() => { const t=(document.body&&document.body.innerText)||''; return JSON.stringify(t.slice(0,3000)); })()""")
            print("\n=== PATH", path, "===")
            print((json.loads(dd2).get("text") if dd2 else "")[:2500], flush=True)
        except Exception as e:
            print("path", path, "err", e, flush=True)
    ws.close()
