#!/usr/bin/env python3
"""Day-14 (2026-10-28) WhatsApp step.

Rules:
  - WA session check FIRST. If the tab shows the QR screen the session is DEAD
    (recurring since 2026-10-24) -> do NOT attempt sends, do NOT mark lead
    statuses, exit with a clear blocker message.
  - If the session is alive: pick up to 10 MOBILE-PREFIX-ONLY candidates from
    today's leads that were never WA-messaged, verify the chat header before
    each send, send, then verify the text landed in the transcript.
  - Row-targeted status updates only (never a full-file rewrite).

Usage: day14_wa_send.py [max_sends]
"""
import sys, os, time, csv, json, re, tempfile
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval
from outreach import wa_send
from templates import build_wa

CSV = '/home/ubuntu/leads.csv'
LOG = '/home/ubuntu/day14_wa_log.txt'
DAY = 'Daily 2026-10-28'
MAX = int(sys.argv[1]) if len(sys.argv) > 1 else 10
TODAY = '2026-10-28'

PERSONAL = ('sayyam', 'shamas', 'afzal', 'chacho nadeem', 'nadeem')
ACTIVE = ('hot lead', 'negotiat', 'sample quote', 'replied', 'follow-up sent')

# mobile prefixes only (landlines never open a WA chat)
MOBILE = (
    '+447', '+346', '+3519', '+393', '+3538', '+316', '+324', '+417', '+436',
    '+3903', '+393', '+41 7', '+417',
)


def log(m):
    line = time.strftime('%H:%M:%S') + ' ' + m
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')


def load():
    with open(CSV, newline='', encoding='utf-8-sig') as f:
        return list(csv.reader(f))


def update_status(lead_id, new_status):
    rows = load()
    idx = {h: i for i, h in enumerate(rows[0])}
    for r in rows[1:]:
        if r and r[0] == lead_id:
            r[idx['Status']] = (r[idx['Status']].rstrip(' |') + ' | ' + new_status)[:250]
    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(rows)
    os.replace(tmp, CSV)


def wa_session_state():
    """Returns (alive:bool, detail:str). Never reloads the WA tab."""
    wa = [t for t in get_tabs() if 'web.whatsapp' in t['url'] and t['type'] == 'page']
    if not wa:
        return False, 'no-wa-tab'
    for t in wa:
        try:
            ws = connect(t)
            v = js_eval(ws, """(() => {
              const txt = document.body ? document.body.innerText : '';
              const qr = /Scan to log in|Scan QR code/i.test(txt);
              const pane = !!document.querySelector('#pane-side');
              return 'qr='+qr+' pane='+pane+' len='+txt.length;
            })()""", await_promise=False)
            ws.close()
            if 'pane=true' in str(v):
                return True, 'live-pane'
        except Exception as e:
            continue
    return False, 'qr-screen (session dead)'


alive, detail = wa_session_state()
log(f'WA SESSION CHECK: alive={alive} ({detail})')
if not alive:
    log('WA SESSION DEAD - skipping all WhatsApp sends, no statuses changed.')
    log('User must re-link WhatsApp Web from phone or VNC screen.')
    sys.exit(2)

rows = load()
idx = {h: i for i, h in enumerate(rows[0])}
targets = []
for r in rows[1:]:
    if len(r) <= idx['Status']:
        continue
    lid = r[0]
    st = (r[idx['Status']] or '')
    sl = st.lower()
    ph = (r[idx['Phone']] or '').strip().replace(' ', '')
    if not ph or len(ph) < 11:
        continue
    if 'whatsapp sent' in sl or 'wa sent' in sl:
        continue
    if 'not on whatsapp' in sl or "isn't on whatsapp" in sl:
        continue
    if any(a in sl for a in ACTIVE):
        continue
    name = (r[idx['Name']] or '')
    if any(p in name.lower() for p in PERSONAL):
        continue
    if TODAY not in sl:
        continue
    if not any(ph.startswith(m.replace(' ', '')) for m in MOBILE):
        continue
    targets.append(r)

log(f'WA candidate leads (mobile-prefix, today, never messaged): {len(targets)}')
targets = targets[:MAX]

sent = notwa = errs = 0
for r in targets:
    lid = r[0]
    name = (r[idx['Name']] or '').replace('&', 'and').strip()
    phone = (r[idx['Phone']] or '').strip().replace(' ', '')
    country = (r[idx['Country']] or 'Europe').strip()
    try:
        alive2, det2 = wa_session_state()
        if not alive2:
            log(f'  WA session died mid-wave at {lid} - stopping, remaining stays queued')
            break
        msg = build_wa(name, f'martial arts training business in {country}')
        wa = [t for t in get_tabs() if 'web.whatsapp' in t['url'] and t['type'] == 'page']
        ws = connect(wa[0])
        cdp = make_cdp(ws)
        cdp('Page.enable')
        cdp('Page.navigate', {'url': f'https://web.whatsapp.com/send?phone={phone}'})
        header = ''
        for _ in range(4):
            time.sleep(7)
            header = js_eval(ws, '(() => { const m = document.querySelector("#main"); return m ? m.innerText.slice(0,80) : ""; })()') or ''
            if header.strip():
                break
        if not header.strip():
            ws.close()
            update_status(lid, f'not on WhatsApp ({DAY})')
            log(f'  NOTWA {lid} {name[:20]} {phone}: chat never opened')
            notwa += 1
            continue
        res = wa_send(phone, msg)
        ok = '"ok":true' in str(res).lower() or "ok': true" in str(res).lower() or 'ok": true' in str(res).lower()
        ws.close()
        if ok:
            update_status(lid, f'WhatsApp sent ({DAY})')
            sent += 1
            log(f'  WA OK {lid} {name[:20]} -> {phone} | header={header[:26]}')
        else:
            update_status(lid, f'WA FAILED ({DAY}): {str(res)[:30]}')
            errs += 1
            log(f'  WA FAIL {lid} {name[:20]} -> {phone}: {str(res)[:50]}')
        time.sleep(35)
    except Exception as e:
        log(f'  WA ERR {lid}: {str(e)[:70]}')
        errs += 1
        time.sleep(8)

log(f'WA DONE: {sent} sent, {notwa} not-on-WA, {errs} errors')
