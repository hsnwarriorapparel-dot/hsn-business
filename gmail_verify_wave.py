#!/usr/bin/env python3
"""Independent Gmail verification of wave sends (no CSV trust) + duplicate probe."""
import json, sys, time
sys.path.insert(0, "/home/ubuntu")
exec(open("/home/ubuntu/cdp_helper.py").read())

tab = find_tab(lambda t: "mail.google.com" in t.get("url", ""))
if not tab:
    print("NO GMAIL TAB"); raise SystemExit
ws = connect(tab)

def sent_count(query):
    try:
        js_eval(ws, "(() => { try{location.hash='#search/'+encodeURIComponent(%s);}catch(e){} return 1;})()" % json.dumps(query))
        time.sleep(6)
        d = js_eval(ws, r"""(() => {
            const t=(document.body&&document.body.innerText)||'';
            const m=t.match(/1-\d+\s+of\s+([\d,]+)\s+Conversations/);
            const m2=t.match(/([\d,]+)\s+Conversations/);
            return JSON.stringify({c1:m?m[1]:null, c2:m2?m2[1]:null, head:t.slice(0,600)});
        })()""")
        return json.loads(d) if d else {}
    except Exception as e:
        return {"err": str(e)[:60]}

for label, q in [
    ("ALL sent last 2d", "in:sent newer_than:2d"),
    ("custom gear subj", 'in:sent newer_than:2d subject:"Custom martial arts gear"'),
    ("club apparel subj", 'in:sent newer_than:2d subject:"custom club apparel"'),
    ("branded uniforms subj", 'in:sent newer_than:2d subject:"Branded uniforms & equipment"'),
    ("club gear mfg subj", 'in:sent newer_than:2d subject:"club gear manufacturing"'),
]:
    r = sent_count(q)
    print(f"{label:26} -> count={r.get('c1') or r.get('c2')}  err={r.get('err','')}")

# duplicate probe on one of tonight's new sends
print("\n=== duplicate probe (should be 1 each) ===")
for addr in ["sanleo.kickboxing@libero.it", "info.bosacademy@gmail.com", "iltempiodelleartimarziali@live.com"]:
    r = sent_count(f"in:sent newer_than:1d to:{addr}")
    print(f"  {addr:45} -> {r.get('c1') or r.get('c2')}")
ws.close()
