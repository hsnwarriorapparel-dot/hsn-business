#!/usr/bin/env python3
"""Send remaining 4 WA to mobile-only gmaps UK leads."""
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

sent_today = set()
for r in rows[1:]:
    if 'Day 8 manual wave' in r[idx['Status']]:
        sent_today.add(r[0])

targets = []
for r in rows[1:]:
    st = r[idx['Status']]
    if 'gmaps' not in st or r[0] in sent_today:
        continue
    ph = (r[idx['Phone']] or '').strip()
    em = (r[idx['Email']] or '').strip()
    if not em or len(ph) < 11:
        continue
    if 'WA' in st or 'WhatsApp' in st:
        continue
    if ph.startswith('+447') or ph.startswith('447') or ph.startswith('+346') or ph.startswith('+3519') or ph.startswith('+393') or ph.startswith('+3538') or ph.startswith('+316'):
        targets.append(r)
    if len(targets) >= 4:
        break

print(f"targets this round: {len(targets)}")
sent = 0
for r in targets:
    lid, name, phone = r[0], r[1].replace('&', 'and'), r[idx['Phone']].strip()
    country = r[idx['Country']] or 'the UK'
    msg = build_wa(name, f"martial arts gym in {country}")
    tab = find_tab(lambda t: 'web.whatsapp' in t['url'] and t['type'] == 'page')
    ws = connect(tab)
    cdp = make_cdp(ws)
    cdp("Page.enable")
    cdp("Page.navigate", {"url": f"https://web.whatsapp.com/send?phone={phone}"})
    header = ""
    for attempt in range(3):
        time.sleep(8)
        header = js_eval(ws, '(() => { const m = document.querySelector("#main"); return m ? m.innerText.slice(0, 60) : ""; })()') or ""
        if header.strip():
            break
    ws.close()
    print(f"{lid} {name[:22]} -> {phone} | header: {header[:28]}")
    if not header.strip():
        print("  skip: chat did not open (likely not on WA)")
        continue
    res = wa_send(phone, msg)
    ok = '"ok":true' in str(res)
    print(f"  send: {'OK' if ok else str(res)[:60]}")
    if ok:
        update_status(lid, f"WA sent (Day 8 manual wave, {time.strftime('%Y-%m-%d')})")
        sent += 1
    time.sleep(35)

print(f"\nDONE: {sent} sent this round")
