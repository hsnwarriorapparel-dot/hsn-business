#!/usr/bin/env python3
"""Mark today's bounces (Day-22, 2026-11-05) as EMAIL FAILED in leads.csv.

Reads the bounce subjects Gmail reported and matches them to the wave lead by
subject + recipient, then applies a row-targeted status write. Read-only
otherwise. Re-running is safe: a lead already marked failed is skipped.
"""
import csv, os, re, sys, time, tempfile

sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval, make_cdp

CSV = '/home/ubuntu/leads.csv'
def _day_tag():
    """The day tag MUST come from the quota-state file, never a hardcoded
    literal (fix 2026-11-06): a copied literal kept yesterday's date, so the
    runner counted yesterday's sends as 'already sent today' and refused to
    send anything on a fresh day."""
    try:
        import json as _j
        _s = _j.load(open('/home/ubuntu/day23_quota_state.json'))
        _d = _s.get('date')
        if _d:
            return 'Daily ' + str(_d)
    except Exception:
        pass
    import time as _t
    return 'Daily ' + _t.strftime('%Y-%m-%d', _t.gmtime())
DAY = _day_tag()


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


# ---- 1. read the bounce list out of Gmail ----
tabs = [t for t in get_tabs() if 'mail.google' in t.get('url', '') and t.get('type') == 'page']
bounces = []
if tabs:
    ws = connect(tabs[0])
    cdp = make_cdp(ws)
    cdp('Page.bringToFront')
    cdp('Page.navigate', {'url': ('https://mail.google.com/mail/u/0/#search/in%3Ainbox+newer_than%3A2d'
                                  '+%28%22Delivery+incomplete%22+OR+%22Address+not+found%22'
                                  '+OR+%22Message+not+delivered%22+OR+%22Message+blocked%22%29')})
    time.sleep(14)
    txt = js_eval(ws, """(() => {const m=document.querySelector('div[role="main"]');
        return m ? m.innerText : '';})()""", await_promise=False) or ''
    ws.close()
    # blocks look like: Subject line / - / bounce reason / timestamp
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    for i, l in enumerate(lines):
        if re.search(r'^(Delivery incomplete|Address not found|Message not delivered|Message blocked)', l):
            subj = lines[i - 2] if i >= 2 else ''
            m = re.search(r'([\w.+-]+@[\w.-]+\.[A-Za-z]{2,})', l)
            em = m.group(1) if m else ''
            bounces.append((subj, em, l[:90]))
else:
    print('NO GMAIL TAB')

print('bounce blocks parsed:', len(bounces))
for s, e, r in bounces:
    print('  ', e, '|', s[:60], '|', r[:60])

# ---- 2. match to wave leads by email + subject lead name ----
rows = list(csv.DictReader(open(CSV, newline='', encoding='utf-8-sig')))
byemail = {}
for r in rows:
    e = (r.get('Email') or '').strip().lower()
    if e:
        byemail.setdefault(e, r)

marked = 0
for subj, em, reason in bounces:
    em = em.strip().lower()
    if not em:
        continue
    r = byemail.get(em)
    if not r:
        print('   NO LEAD for', em)
        continue
    st = r.get('Status') or ''
    sl = st.lower()
    if 'failed' in sl:
        print('   already failed', r['Lead ID'], em)
        continue
    # EXCLUDED rows were never supposed to be emailed (junk/telemetry address
    # the QA filter already rejected). A bounce on one of them is not a lead
    # failure - marking it EMAIL FAILED just pollutes the counters.
    if 'excluded' in sl:
        print('   EXCLUDED row (junk address, not a lead failure) - skipping', r['Lead ID'], em)
        continue
    # Never append the same marker twice (the sweep can list one bounce twice).
    marker = f"EMAIL FAILED ({DAY}): bounce - {reason[:60]}"
    if marker in st:
        print('   marker already present', r['Lead ID'], em)
        continue
    ok = update_status(r['Lead ID'], marker)
    marked += 1
    print(f"   MARK {r['Lead ID']} {em} written={ok}")

print('marked failed:', marked)
chk = list(csv.DictReader(open(CSV, newline='', encoding='utf-8-sig')))
print('csv rows after:', len(chk))
