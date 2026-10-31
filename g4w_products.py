#!/usr/bin/env python3
"""Read g4w dashboard: product count + any received inquiries (read-only navigation)."""
import json, sys, time
sys.path.insert(0, "/home/ubuntu")
exec(open("/home/ubuntu/cdp_helper.py").read())

tab = find_tab(lambda t: "go4worldbusiness.com/member/dashboard" in t.get("url", "").lower())
if not tab:
    print("NO G4W TAB"); raise SystemExit
ws = connect(tab)
cdp = make_cdp(ws)
cdp("Page.navigate", {"url": "https://www.go4worldbusiness.com/member/dashboard/"})
time.sleep(9)
d = js_eval(ws, r"""(() => {
    const t=(document.body&&document.body.innerText)||'';
    const links=[];
    document.querySelectorAll('a[href*="dashboard"], a[href*="member"]').forEach(a=>{
        const h=a.getAttribute('href')||''; const x=(a.innerText||'').trim();
        if(h && x && links.length<40) links.push(x.slice(0,30)+' :: '+h.slice(0,70));
    });
    return JSON.stringify({url:location.href, text:t.slice(0,2600), links:links});
})()""")
dd = json.loads(d) if d else {}
print("URL:", dd.get("url"))
print("\n=== DASHBOARD ===")
print(dd.get("text", "")[:2600])
print("\n=== NAV LINKS ===")
for l in dd.get("links", [])[:35]:
    print(" ", l)
ws.close()
