#!/usr/bin/env python3
"""Read specific Gmail threads: The Dungeon g4w inquiry, Alvaro, any human-ish reply. Read-only."""
import json, sys, time
sys.path.insert(0, "/home/ubuntu")
exec(open("/home/ubuntu/cdp_helper.py").read())

tab = find_tab(lambda t: "mail.google.com" in t.get("url", ""))
if not tab:
    print("NO GMAIL TAB")
    raise SystemExit
ws = connect(tab)

def search(q, label):
    print(f"\n########## {label} :: {q}")
    try:
        js_eval(ws, "(() => { try{location.hash='#search/'+encodeURIComponent(%s);}catch(e){} return 1;})()" % json.dumps(q))
        time.sleep(6)
        rows = js_eval(ws, r"""(() => {
            const out=[];
            document.querySelectorAll('tr').forEach(tr=>{
              const fe=tr.querySelector('span[email]');
              const tx=(tr.innerText||'').trim().replace(/\n+/g,' | ');
              if(tx) out.push((fe?fe.getAttribute('email')+' :: ':'')+tx.slice(0,350));
            });
            return JSON.stringify(out.slice(0,15));
        })()""")
        print(json.loads(rows) if rows else "[]")
    except Exception as e:
        print("ERR", e)

search("The Dungeon", "G4W INQUIRY")
search("from:pt.alvarocampeao@gmail.com", "ALVARO")
search("in:inbox newer_than:5d -from:mailer-daemon -from:postmaster", "RECENT INBOX")
search("in:sent newer_than:2d subject:\"Custom martial arts gear\"", "SENT 2D")

# Alvaro full thread body if present
try:
    js_eval(ws, "(() => { try{location.hash='#search/'+encodeURIComponent('alvaro');}catch(e){} return 1;})()")
    time.sleep(6)
    body = js_eval(ws, r"""(() => {
        const t=(document.body&&document.body.innerText)||'';
        return t.slice(0,4000);
    })()""")
    print("\n########## ALVARO THREAD RAW\n", (body or "")[:3500])
except Exception as e:
    print("alvaro body err", e)
ws.close()
