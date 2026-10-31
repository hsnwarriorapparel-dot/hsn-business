#!/usr/bin/env python3
"""Post-wave cleanup + reply sweep for Day-16 (2026-10-30).

1. Mark the STOP reply (Goshin Karate, L2207) as DO-NOT-CONTACT.
2. Sweep Gmail for human client replies (excludes bounces, auto-acks, platform mail).
3. Print final counters from hsn_counters.py.

MUST run only AFTER the email wave finishes (it writes leads.csv).
"""
import csv, os, re, sys, json, time, tempfile
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval, make_cdp

CSV = '/home/ubuntu/leads.csv'
DAY = 'Daily 2026-10-30'


def log(m):
    print(time.strftime('%H:%M:%S') + ' ' + m, flush=True)


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


# ---------- 1. STOP / do-not-contact + client reply markers ----------
log('--- marking STOP replies / client replies in leads.csv ---')
STOP_LEADS = [
    ('L2207', 'Goshin Karate & Judo Academy', 'info@goshinkarate.com',
     'STOP reply received 2026-10-29 (opted out). No further email/IG/WA.'),
]
for lid, name, em, note in STOP_LEADS:
    ok = update_status(lid, f'DO NOT CONTACT: {note}')
    log(f'  {lid} {name} <{em}> -> DO NOT CONTACT (written={ok})')

# IG replies found in the 2026-10-30 sweep (draft-only, never auto-sent)
REPLY_LEADS = [
    ('L1376', 'Boxeo El Rayo - MMA, Muay-Thai, Defensa Personal',
     'REPLIED (IG 2026-10-30): human reply in Spanish - gave direct contact for Pedro (625 264 990 / 914 774 879). '
     'Awaiting user approval to reply.'),
    ('L2068', 'Active Jiu Jitsu Houston',
     'IG REPLY 2026-10-30: auto-acknowledgement only ("we have received your message"). Not a human reply.'),
]
for lid, name, note in REPLY_LEADS:
    ok = update_status(lid, note)
    log(f'  {lid} {name} -> reply marker written={ok}')

chk = list(csv.DictReader(open(CSV, newline='', encoding='utf-8-sig')))
for r in chk:
    if r['Lead ID'] in ('L2207', 'L1376', 'L2068'):
        log('  VERIFY', r['Lead ID'] + ':', r['Status'][-150:])

# ---------- 2. Gmail reply sweep ----------
log('--- Gmail reply sweep ---')
tabs = get_tabs()
gm = [t for t in tabs if 'mail.google' in t.get('url', '') and t.get('type') == 'page']
if not gm:
    log('  NO GMAIL TAB - cannot sweep')
else:
    ws = connect(gm[0])
    cdp = make_cdp(ws)
    cdp('Page.bringToFront')
    # remove the Google feedback overlay (blocks compose / clicks)
    js_eval(ws, """(() => {let n=0;for (const f of document.querySelectorAll('iframe')) {
        if (/aloha_frame|feedback\\//i.test(f.src||'')) { f.remove(); n++; }} return n;})()""",
            await_promise=False)
    url = ('https://mail.google.com/mail/u/0/#search/in%3Ainbox+newer_than%3A7d'
           '-from%3Amailer-daemon+-from%3Apostmaster+-from%3Anoreply'
           '-from%3A(no-reply)+-from%3A(notifications%40)+-from%3A(google.com)'
           '-from%3A(tradewheel)+-from%3A(go4worldbusiness)+-from%3A(facebook)'
           '-from%3A(instagram)')
    cdp('Page.navigate', {'url': url})
    time.sleep(12)
    txt = js_eval(ws, """(() => {const m=document.querySelector('div[role="main]');
        return m ? m.innerText : '';})()""", await_promise=False) or ''
    log('  inbox 7d window:')
    for line in txt.splitlines():
        if line.strip():
            log('    | ' + line.strip()[:150])

    # count conversations
    m = re.search(r'([\d,]+)\s*[-–]\s*([\d,]+)\s+of\s+([\d,]+)\s+Conversations', txt)
    if m:
        log(f'  conversations in window: {m.group(3)}')

    # look for STOP / unsubscribe keywords across all inbox mail
    cdp('Page.navigate', {'url': 'https://mail.google.com/mail/u/0/#search/in%3Ainbox+newer_than%3A30d'})
    time.sleep(10)
    txt2 = js_eval(ws, """(() => {const m=document.querySelector('div[role="main"]');
        return m ? m.innerText : '';})()""", await_promise=False) or ''
    for kw in ('STOP', 'unsubscribe', 'remove me', 'do not contact', 'no thanks'):
        for line in txt2.splitlines():
            if kw.lower() in line.lower():
                log(f'  KEYWORD {kw!r}: {line.strip()[:160]}')
    ws.close()

# ---------- 3. final counters ----------
log('--- final counters ---')
try:
    import hsn_counters
    for fn in ('count',):
        pass
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        hsn_counters.__name__ = '__main__'
        import runpy
        runpy.run_path('/home/ubuntu/hsn_counters.py', run_name='__main__')
    for line in buf.getvalue().splitlines():
        log('  ' + line)
except Exception as e:
    log('  hsn_counters error:', str(e)[:120])
log('=== DAY16 REPLY SWEEP DONE ===')
