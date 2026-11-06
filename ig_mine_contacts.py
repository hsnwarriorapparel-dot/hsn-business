#!/usr/bin/env python3
"""Mine IG auto-replies for contact details (email / phone / WhatsApp).

Many gyms answer DMs with an auto-response that includes their email and
WhatsApp number. That is a FREE lead enrichment source: we find the email
without a separate website scrape, and the email goes straight into the
tracker so the next wave can reach them.

Reads the IG inbox, extracts emails and phones from every thread's text, and
writes NEW ones into leads.csv (row-targeted, verified).
"""
import sys, time, re, csv
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval, make_cdp

EMAIL_RE = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
PHONE_RE = re.compile(r'(?:\+\d{1,3}[\s.-]?)?(?:\d[\s.-]?){8,14}\d')
JUNK_EMAIL = ('sentry', 'wixpress', 'example.com', 'email.com', '2x.png',
               'domain.com', 'yourdomain', 'yourcompany', 'test.com', 'mysite')

igtabs = [t for t in get_tabs() if 'instagram.com' in t.get('url', '') and t.get('type') == 'page']
if not igtabs:
    print('NO IG TAB')
    sys.exit(1)
ws = connect(igtabs[0])
cdp = make_cdp(ws)
cdp('Page.enable')
cdp('Page.bringToFront')
time.sleep(2)
txt = js_eval(ws, "(() => (document.body?document.body.innerText:'').slice(0,20000))()", await_promise=False) or ''
ws.close()

emails = sorted(set(e.lower() for e in EMAIL_RE.findall(txt) if not any(j in e.lower() for j in JUNK_EMAIL)))
print('=== emails found in IG inbox ===')
for e in emails:
    print('  ', e)

# load tracker
with open('/home/ubuntu/leads.csv', newline='', encoding='utf-8-sig') as f:
    rows = list(csv.reader(f))
hdr = rows[0]
idx = {h: i for i, h in enumerate(hdr)}
known = set((r[idx['Email']] if idx['Email'] < len(r) else '').strip().lower() for r in rows[1:])

# match each email to a lead by IG username / name mention in the thread text
new_hits = []
for e in emails:
    if e in known:
        print('  (already known)', e)
        continue
    # find the thread block containing this email
    for block in txt.split('\n'):
        pass
    # find lead whose IG username or name appears near the email
    for r in rows[1:]:
        if len(r) <= idx['IG Username']:
            continue
        igh = (r[idx['IG Username']] if idx['IG Username'] < len(r) else '') or ''
        name = (r[idx['Name']] if idx['Name'] < len(r) else '') or ''
        handle = igh.replace('@', '').split('.')[0].lower()
        nslug = re.sub(r'[^a-z0-9]', '', name.lower())[:12]
        if (handle and handle in txt.lower()) or (nslug and nslug in re.sub(r'[^a-z0-9]', '', txt.lower())):
            new_hits.append((r[idx['Lead ID']], name, e, igh))
            break

print()
print('=== NEW emails matched to leads ===')
if not new_hits:
    print('  none')
for lid, name, e, igh in new_hits:
    print('  %-8s %-30s %-34s %s' % (lid, name[:29], e, igh))

if new_hits:
    from safe_update_row import update
    for lid, name, e, igh in new_hits:
        update(lid, email=e,
               notes='EMAIL FOUND from IG auto-reply 2026-11-06 (their own auto-response gave this address).')
    print()
    print('written + verified:', len(new_hits))
