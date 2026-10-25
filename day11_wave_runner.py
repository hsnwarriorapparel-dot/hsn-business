#!/usr/bin/env python3
"""Day-11 (2026-10-25) email wave runner.
Sends the quality-ranked wave in /home/ubuntu/day11_wave.txt at Gmail-safe 38s
pacing. Marks each lead's Status IMMEDIATELY after its send (row-targeted read
-> write -> atomic replace), so a re-run resumes exactly where it stopped and
never double-sends. Per-lead failure reasons are recorded, not swallowed.
"""
import sys, os, time, csv, tempfile
sys.path.insert(0, '/home/ubuntu')
from outreach import gmail_send
from templates import build_email
from cdp_helper import get_tabs, connect, js_eval

CSV = '/home/ubuntu/leads.csv'
LOG = '/home/ubuntu/day11_log.txt'
WAVE = '/home/ubuntu/day11_wave.txt'
PACE = 38
DAY = 'Daily 2026-10-25'


def log(m):
    line = time.strftime('%H:%M:%S') + ' ' + m
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')


def load():
    with open(CSV, newline='', encoding='utf-8') as f:
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


def already_sent(lid):
    rows = load()
    idx = {h: i for i, h in enumerate(rows[0])}
    for r in rows[1:]:
        if r and r[0] == lid:
            return 'email sent' in (r[idx['Status']] or '').lower()
    return False


def gmail_ready():
    try:
        tabs = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
        if not tabs:
            return False, 'no-gmail-tab'
        ws = connect(tabs[0])
        v = js_eval(ws, """(() => {
          const btn = Array.from(document.querySelectorAll('div[role="button"], .T-I')).find(e => /^Compose$/i.test((e.innerText||'').trim()));
          return btn ? 'ready' : 'no-compose-button';
        })()""", await_promise=False)
        ws.close()
        return v == 'ready', v
    except Exception as e:
        return False, f'probe-error:{str(e)[:60]}'


ids = [l.strip() for l in open(WAVE) if l.strip()]
log(f"DAY11 WAVE START: {len(ids)} leads from {WAVE}")

rows = load()
idx = {h: i for i, h in enumerate(rows[0])}
iE, iN, iC, iCi, iS = (idx['Email'], idx['Name'], idx['Country'], idx['City'], idx['Status'])
meta = {}
for r in rows[1:]:
    if r and r[0] in ids:
        meta[r[0]] = r

sent = failed = skipped = 0
for pos, lid in enumerate(ids, 1):
    r = meta.get(lid)
    if not r:
        log(f"  SKIP {lid}: not in CSV")
        skipped += 1
        continue
    if already_sent(lid):
        log(f"  SKIP {lid} ({(r[iN] or '')[:20]}): already marked email sent")
        skipped += 1
        continue
    ok_gmail, state = gmail_ready()
    if not ok_gmail:
        log(f"  GMAIL NOT READY ({state}) at {lid} - stopping, will resume from here")
        log(f"PAUSED after {sent} sent, {failed} failed, {skipped} skipped")
        break

    name = (r[iN] or '').strip().replace('&', 'and')
    email = (r[iE] or '').strip().lower()
    country = (r[iC] or '').strip() or 'Europe'
    city = (r[iCi] or '').strip()
    region = 'USA' if country == 'USA' else 'Europe'
    detail = f"martial arts and boxing gym in {city}" if city else f"martial arts and boxing gym in {country}"
    try:
        subject, body = build_email(name, detail, region=region)
        res = gmail_send(email, subject, body)
        ok = res.get('ok') if isinstance(res, dict) else ('sent' in str(res).lower())
        log(f"  [{pos}/{len(ids)}] EMAIL {lid} {name[:22]} -> {email}: {'OK' if ok else str(res)[:60]}")
        if ok:
            update_status(lid, f"COMPLETE: email sent ({DAY})")
            sent += 1
        else:
            update_status(lid, f"EMAIL FAILED ({DAY}): {str(res)[:40]}")
            failed += 1
    except Exception as e:
        log(f"  [{pos}/{len(ids)}] EMAIL ERR {lid}: {str(e)[:70]}")
        update_status(lid, f"EMAIL FAILED ({DAY}): exception {str(e)[:20]}")
        failed += 1
    time.sleep(PACE)

log(f"DAY11 WAVE COMPLETE: {sent} sent, {failed} failed, {skipped} skipped")
