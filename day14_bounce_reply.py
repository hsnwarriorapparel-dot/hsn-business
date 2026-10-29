#!/usr/bin/env python3
"""Day-14 focused checks:
  1. REAL bounces in the last 1d (mailer-daemon) - read the thread body to get
     the exact bounced address, so it can be marked EMAIL FAILED (never re-sent)
  2. NEW inbound human replies since Day-13 (newer_than:1d, excluding auto-acks)
  3. Go4WorldBusiness thread status (live marketplace channel)
READ-ONLY. Client replies are draft-only.
"""
import sys, json, time, re, urllib.parse
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

PERSONAL = re.compile(r'sayyam|shamas|afzal|chacho|bhai', re.I)
AUTOMAIL = re.compile(r'mailer-daemon|postmaster|mail-daemon|noreply|no-reply|'
                      r'notifications@|support@|bounce|mailer@|'
                      r'hsnwarriorapparel@gmail\.com|'
                      r'donotreply|appointlet|memeditingteam', re.I)
# auto-ack phrases that mean "no human wrote this"
AUTO_ACK = re.compile(r'automatic reply|autoreply|auto-reply|thank you for reaching out|'
                       r'wir melden uns|wir haben deine nachricht erhalten|'
                       r'thank you for your email|i will endeavour|'
                       r'vielen dank für ihre nachricht|we have received your message|'
                       r'this is an automated|we will respond as soon as we can', re.I)

tabs = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
if not tabs:
    print('NO GMAIL TAB')
    sys.exit(1)
ws = connect(tabs[0])
cdp = make_cdp(ws)
cdp('Page.enable')
cdp('Page.bringToFront')
time.sleep(1)


def goto(q):
    cdp('Page.navigate', {'url': 'https://mail.google.com/mail/u/0/#search/' + urllib.parse.quote(q)})
    time.sleep(5)


def rows(q):
    goto(q)
    v = js_eval(ws, """(() => {
        const spans = Array.from(document.querySelectorAll('span[email]'));
        const seen = new Set(); const out = [];
        for (const s of spans) {
            const from = s.getAttribute('email') || '';
            if (!from || seen.has(from)) continue;
            seen.add(from);
            let row = s.closest('div[role="listitem"]') || s.closest('div.adn.ads') || s.closest('tr');
            const txt = row ? (row.innerText || '').replace(/\\s+/g,' ').trim() : '';
            const subjEl = row ? row.querySelector('span[data-thread-subject]') : null;
            out.push({from: from, subject: subjEl ? (subjEl.innerText||'') : '', snippet: txt.slice(0,300)});
        }
        const main = document.querySelector('div[role="main"]');
        const mt = main ? (main.innerText||'').replace(/\\s+/g,' ') : '';
        const m = mt.match(/(\\d+)\\s*[–-]\\s*\\d+\\s+of\\s+(\\d+)/);
        return JSON.stringify({items: out.slice(0,40), head: mt.slice(0,180),
                               count: m ? m[2] : null});
    })()""", await_promise=False)
    try:
        return json.loads(v or '{}')
    except Exception:
        return {}


print('=== 1. BOUNCES (last 1d, mailer-daemon / delivery-status) ===')
bounce_rows = []
for q in ['newer_than:1d from:mailer-daemon@google.com',
          'newer_than:1d (subject:"Delivery Status Notification" OR subject:"Delivery incomplete" '
          'OR subject:"Address not found" OR subject:"Message blocked")']:
    r = rows(q)
    print(f"  [{q[:46]}] count={r.get('count')} head={r.get('head','')[:110]}")
    for it in r.get('items', []):
        if PERSONAL.search(it['from']):
            continue
        bounce_rows.append(it)
        print('   BNC:', it['from'], '|', it['subject'][:60], '|', it['snippet'][:180])

print()
print('=== 2. NEW INBOUND (last 1d) - human vs auto ===')
new_in = []
for q in ['newer_than:1d -from:me -from:mailer-daemon@google.com -from:postmaster']:
    r = rows(q)
    print(f"  [{q[:46]}] count={r.get('count')} head={r.get('head','')[:110]}")
    for it in r.get('items', []):
        if PERSONAL.search(it['from']):
            continue
        auto = bool(AUTOMAIL.search(it['subject'] + ' ' + it['snippet']))
        tag = 'AUTO-ACK' if auto else '*** HUMAN CANDIDATE ***'
        print(f'   {tag} | {it["from"]} | {it["subject"][:60]} | {it["snippet"][:150]}')
        if not auto:
            new_in.append(it)

print()
print('=== 3. Go4WorldBusiness thread (live marketplace) ===')
g = rows('newer_than:7d from:go4worldbusiness.com')
for it in g.get('items', []):
    print('   G4WB:', it['from'], '|', it['subject'][:70], '|', it['snippet'][:170])

print()
print('HUMAN REPLY CANDIDATES:', len(new_in))
for it in new_in:
    print('   *', it['from'], '|', it['subject'][:90], '|', it['snippet'][:260])

json.dump({'bounces': bounce_rows, 'human_replies': new_in},
          open('/home/ubuntu/day14_bounce_reply.json', 'w'), indent=1)
ws.close()
print('written /home/ubuntu/day14_bounce_reply.json')
