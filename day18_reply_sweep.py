#!/usr/bin/env python3
"""Day-18 (2026-11-01) reply sweep + final verification.

Runs AFTER the email wave. Sweeps Gmail for human client replies (excluding
bounces, auto-acks and platform mail) and IG for replies, then prints the
canonical counters. Read-only on leads.csv except for reply markers.
"""
import csv, os, re, sys, json, time, tempfile
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval, make_cdp

CSV = '/home/ubuntu/leads.csv'
DAY = 'Daily 2026-11-01'
LOG = '/home/ubuntu/day18_reply_sweep_log.txt'


def log(m):
    line = time.strftime('%H:%M:%S') + ' ' + m
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')


def update_status(lead_id, new_status):
    rows = list(csv.reader(open(CSV, newline='', encoding='utf-8-sig')))
    idx = {h: i for i, h in enumerate(rows[0])}
    hit = False
    for r in rows[1:]:
        if r and r[0] == lead_id:
            r[idx['Status']] = (r[idx['Status']].rstrip(' |') + ' | ' + new_status)[:250]
            hit = True
    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(rows)
    os.replace(tmp, CSV)
    return hit


# ---------- 1. Gmail reply sweep ----------
log('--- Gmail reply sweep (7d) ---')
tabs = get_tabs()
gm = [t for t in tabs if 'mail.google' in t.get('url', '') and t.get('type') == 'page']
if not gm:
    log('  NO GMAIL TAB - cannot sweep')
else:
    ws = connect(gm[0])
    cdp = make_cdp(ws)
    cdp('Page.bringToFront')
    js_eval(ws, """(() => {let n=0;for (const f of document.querySelectorAll('iframe')) {
        if (/aloha_frame|feedback\\//i.test(f.src||'')) { f.remove(); n++; }} return n;})()""",
           await_promise=False)
    url = ('https://mail.google.com/mail/u/0/#search/in%3Ainbox+newer_than%3A7d'
           '-from%3Amailer-daemon+-from%3Apostmaster+-from%3Anoreply'
           '-from%3A(no-reply)+-from%3A(notifications%40)+-from%3A(google.com)'
           '-from%3A(tradewheel)+-from%3A(go4worldbusiness)+-from%3A(facebook)'
           '-from%3A(instagram)')
    cdp('Page.navigate', {'url': url})
    time.sleep(14)
    txt = js_eval(ws, """(() => {const m=document.querySelector('div[role="main]');
        return m ? m.innerText : '';})()""", await_promise=False) or ''
    log('  inbox 7d window rows:')
    for line in txt.splitlines():
        if line.strip():
            log('    | ' + line.strip()[:150])

    m = re.search(r'([\d,]+)\s*[-–]\s*([\d,]+)\s+of\s+([\d,]+)\s+Conversations', txt)
    if m:
        log(f'  conversations in 7d window: {m.group(3)}')

    # STOP / opt-out keyword scan over a wider window
    cdp('Page.navigate', {'url': 'https://mail.google.com/mail/u/0/#search/in%3Ainbox+newer_than%3A30d'})
    time.sleep(12)
    txt2 = js_eval(ws, """(() => {const m=document.querySelector('div[role="main"]');
        return m ? m.innerText : '';})()""", await_promise=False) or ''
    for kw in ('STOP', 'unsubscribe', 'remove me', 'do not contact', 'no thanks'):
        for line in txt2.splitlines():
            if kw.lower() in line.lower():
                log(f'  KEYWORD {kw!r}: {line.strip()[:160]}')

    # bounces in the last 2 days
    cdp('Page.navigate', {'url': ('https://mail.google.com/mail/u/0/#search/in%3Ainbox+newer_than%3A2d'
                                  '+%28%22Delivery+incomplete%22+OR+%22Address+not+found%22'
                                  '+OR+%22Message+not+delivered%22+OR+%22Message+blocked%22%29')})
    time.sleep(12)
    txt3 = js_eval(ws, """(() => {const m=document.querySelector('div[role="main"]');
        return m ? m.innerText : '';})()""", await_promise=False) or ''
    mb = re.search(r'([\d,]+)\s*[-–]\s*([\d,]+)\s+of\s+([\d,]+)\s+Conversations', txt3)
    if mb:
        log(f'  bounce/undeliverable conversations in 2d window: {mb.group(3)}')
    for line in txt3.splitlines():
        if line.strip():
            log('    B| ' + line.strip()[:140])
    ws.close()

# ---------- 2. IG inbox sweep for replies ----------
log('--- IG inbox reply sweep ---')
try:
    igtabs = [t for t in get_tabs() if 'instagram.com/direct/inbox' in t.get('url', '')
              and t.get('type') == 'page']
    if not igtabs:
        log('  no IG inbox tab')
    else:
        ws = connect(igtabs[0])
        cdp = make_cdp(ws)
        cdp('Page.bringToFront')
        cdp('Page.navigate', {'url': 'https://www.instagram.com/direct/inbox/'})
        time.sleep(10)
        itxt = js_eval(ws, """(() => (document.body?document.body.innerText:'').slice(0,4000))()""",
                       await_promise=False) or ''
        for line in itxt.splitlines():
            if line.strip():
                log('    IG| ' + line.strip()[:140])
        ws.close()
except Exception as e:
    log('  IG sweep error: ' + str(e)[:120])

# ---------- 3. canonical counters ----------
log('--- final counters ---')
try:
    import io, contextlib, runpy
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        runpy.run_path('/home/ubuntu/hsn_counters.py', run_name='__main__')
    for line in buf.getvalue().splitlines():
        log('  ' + line)
except Exception as e:
    log('  hsn_counters error: ' + str(e)[:120])
log('=== DAY18 REPLY SWEEP DONE ===')
