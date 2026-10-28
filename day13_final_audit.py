#!/usr/bin/env python3
"""Final independent Gmail audit for the Day-13 wave:
  1. every wave recipient checked with `in:sent to:<email>` -> duplicates?
  2. bounces in the last 2 days (mailer-daemon) -> real failures?
  3. subject-variant conversation counts
Reads Gmail, not the CSV, so a clobbered marker cannot hide a problem.
"""
import sys, json, time, csv, urllib.parse
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

CSV = '/home/ubuntu/leads.csv'
WAVE = '/home/ubuntu/day13_wave.txt'
SUBJECT_FRAGMENTS = ["Custom martial arts gear for", "club gear manufacturing for",
                     "Branded uniforms & equipment for", "custom club apparel"]

tabs = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
if not tabs:
    print('NO GMAIL TAB')
    sys.exit(1)
ws = connect(tabs[0])
cdp = make_cdp(ws)


def search(q, wait=4.0):
    url = 'https://mail.google.com/mail/u/0/#search/' + urllib.parse.quote(q)
    cdp('Page.navigate', {'url': url})
    time.sleep(wait)
    v = js_eval(ws, """(() => {
        const main = document.querySelector('div[role="main"]');
        const txt = main ? main.innerText : '';
        const m = txt.match(/(\\d+)\\s*[–-]\\s*\\d+\\s+of\\s+(\\d+)/);
        return JSON.stringify({count: m ? m[2] : null, text: txt.replace(/\\s+/g,' ').slice(0,500)});
    })()""", await_promise=False)
    return json.loads(v or '{}')


print('=== 1. DUPLICATE PROBE over all 100 wave recipients ===')
rows = list(csv.DictReader(open(CSV, newline='', encoding='utf-8')))
d = {r['Lead ID']: r for r in rows}
wave = [l.strip() for l in open(WAVE) if l.strip()]
dups, missing = [], []
for i, lid in enumerate(wave, 1):
    email = (d.get(lid, {}).get('Email') or '').strip().lower()
    if not email:
        missing.append((lid, 'no email'))
        continue
    r = search('in:sent newer_than:1d to:' + email, wait=3.2)
    n = int(r.get('count') or 0)
    if n > 1:
        dups.append((lid, email, n))
    elif n == 0:
        missing.append((lid, email))
    if i % 20 == 0:
        print(f'  checked {i}/100 ...', flush=True)
print('  duplicates:', len(dups), dups)
print('  NOT found in Sent:', len(missing), missing)
print('  clean recipients:', 100 - len(dups) - len(missing))

print()
print('=== 2. SUBJECT-VARIANT CONVERSATION COUNTS (in:sent newer_than:1d) ===')
tot = 0
for s in SUBJECT_FRAGMENTS:
    r = search('in:sent newer_than:1d subject:"' + s + '"')
    n = int(r.get('count') or 0)
    tot += n
    print(f'  {n:>4}  |  {s}')
print('  TOTAL:', tot)

print()
print('=== 3. BOUNCES in last 2 days ===')
r = search('newer_than:2d (from:mailer-daemon OR from:postmaster OR subject:"Delivery incomplete" OR subject:"Address not found")')
print('  bounce threads:', r.get('count'), '|', (r.get('text') or '')[:400])

print()
print('=== 4. HUMAN REPLIES (newer_than:2d, -from:me) ===')
r = search('newer_than:2d -from:me -from:mailer-daemon -from:postmaster')
print('  threads:', r.get('count'), '|', (r.get('text') or '')[:600])
ws.close()
