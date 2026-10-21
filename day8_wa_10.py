#!/usr/bin/env python3
"""Send 10 WA messages to fresh gmaps UK leads (never contacted, have phone + email).
Verify-first protocol on every send."""
import sys, time, json, csv, os, tempfile
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import *
from outreach import wa_send
from templates import build_wa

def update_status(lead_id, new_status):
    with open('/home/ubuntu/leads.csv') as f:
        rows = list(csv.reader(f))
    idx = {h: i for i, h in enumerate(rows[0])}
    for r in rows[1:]:
        if r[0] == lead_id:
            r[idx['Status']] = (r[idx['Status']] + ' | ' + new_status)[:250]
    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='') as f:
        csv.writer(f).writerows(rows)
    with open(tmp) as f:
        assert len(list(csv.reader(f))) == len(rows)
    os.replace(tmp, '/home/ubuntu/leads.csv')

rows = list(csv.reader(open('/home/ubuntu/leads.csv')))
idx = {h: i for i, h in enumerate(rows[0])}

# fresh gmaps leads: have phone (>=11 digits), never WA'd (no WA/WhatsApp marker), have email
cands = []
for r in rows[1:]:
    st = r[idx['Status']]
    if 'gmaps' not in st:
        continue
    ph = (r[idx['Phone']] or '').strip()
    em = (r[idx['Email']] or '').strip()
    if len(ph) < 11 or not em:
        continue
    if 'WA' in st or 'WhatsApp' in st or 'wa=' in st.lower():
        continue
    cands.append(r)

print(f"candidates: {len(cands)}")
targets = cands[:10]
# skip any already WA'd today
sent_ids = set()
import csv as _c
for _r in _c.reader(open('/home/ubuntu/leads.csv')):
    if 'Day 8 manual wave' in (_r[11] if len(_r) > 11 else ''):
        sent_ids.add(_r[0])
targets = [t for t in targets if t[0] not in sent_ids][:10]
sent = 0
for r in targets:
    lid, name, phone = r[0], r[1].replace('&', 'and'), r[idx['Phone']].strip()
    country = r[idx['Country']] or 'the UK'
    msg = build_wa(name, f"martial arts gym in {country}")
    # STEP 1: verify header
    tab = find_tab(lambda t: 'web.whatsapp' in t['url'] and t['type'] == 'page')
    ws = connect(tab)
    cdp = make_cdp(ws)
    cdp("Page.enable")
    cdp("Page.navigate", {"url": f"https://web.whatsapp.com/send?phone={phone}"})
    header = ""
    for attempt in range(4):  # wait up to 24s for chat to render
        time.sleep(8)
        header = js_eval(ws, '(() => { const m = document.querySelector("#main"); return m ? m.innerText.slice(0, 60) : ""; })()') or ""
        if header.strip():
            break
    ws.close()
    ok_hdr = phone[-9:] in header.replace(' ', '') or 'click here' in header or len(header.strip()) > 3
    print(f"{lid} {name[:20]} -> {phone} | header: {header[:30]}")
    if not ok_hdr:
        print("  ABORT: chat did not open")
        continue
    # STEP 2: send
    res = wa_send(phone, msg)
    ok = '"ok":true' in str(res)
    print(f"  send: {'OK' if ok else str(res)[:60]}")
    if ok:
        update_status(lid, f"WA sent (Day 8 manual wave, {time.strftime('%Y-%m-%d')})")
        sent += 1
    time.sleep(35)

print(f"\nDONE: {sent}/10 sent")
