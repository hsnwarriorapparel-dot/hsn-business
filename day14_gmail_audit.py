#!/usr/bin/env python3
"""Day-14 (2026-10-28) independent Gmail Sent audit + duplicate probe + bounce
detection + client-reply sweep.

READ-ONLY for replies: this NEVER sends. Client replies are draft-only until
the user says "send". Personal contacts are filtered out entirely.

Run AFTER the email wave is finished (it navigates the Gmail tab).
"""
import sys, json, time, csv, re, urllib.parse
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

CSV = '/home/ubuntu/leads.csv'
WAVE = '/home/ubuntu/day14_wave.txt'
DAY = '2026-10-28'

PERSONAL = re.compile(r'sayyam|shamas|afzal|chacho|bhai', re.I)
AUTOMAIL = re.compile(r'mailer-daemon|postmaster|mail-daemon|noreply|no-reply|'
                      r'notifications@google|support@|bounce|mailer@|'
                      r'hsnwarriorapparel@gmail\.com', re.I)

tabs = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
if not tabs:
    print('NO GMAIL TAB')
    sys.exit(1)
ws = connect(tabs[0])
cdp = make_cdp(ws)
cdp('Page.enable')
cdp('Page.bringToFront')
time.sleep(1)


def search(q):
    url = 'https://mail.google.com/mail/u/0/#search/' + urllib.parse.quote(q)
    cdp('Page.navigate', {'url': url})
    time.sleep(4.5)
    v = js_eval(ws, """(() => {
        const main = document.querySelector('div[role="main"]');
        const txt = main ? main.innerText : '';
        const m = txt.match(/(\\d+)\\s*[–-]\\s*\\d+\\s+of\\s+(\\d+)/);
        return JSON.stringify({count: m ? m[2] : null});
    })()""", await_promise=False)
    return int(json.loads(v or '{}').get('count') or 0)


def search_rows(q):
    """Return the visible row list (from/subject/snippet) for a query."""
    url = 'https://mail.google.com/mail/u/0/#search/' + urllib.parse.quote(q)
    cdp('Page.navigate', {'url': url})
    time.sleep(5)
    v = js_eval(ws, """(() => {
        const spans = Array.from(document.querySelectorAll('span[email]'));
        const seen = new Set();
        const out = [];
        for (const s of spans) {
            const from = s.getAttribute('email') || '';
            if (!from || seen.has(from)) continue;
            seen.add(from);
            let row = s.closest('div[role="listitem"]') || s.closest('div.adn.ads') ||
                      s.closest('tr') || s.closest('div');
            const txt = row ? (row.innerText || '').replace(/\\s+/g,' ').trim() : '';
            const subjEl = row ? row.querySelector('span[data-thread-subject]') : null;
            out.push({from: from,
                      subject: subjEl ? (subjEl.innerText || '') : '',
                      snippet: txt.slice(0, 260)});
        }
        const main = document.querySelector('div[role="main"]');
        return JSON.stringify({items: out.slice(0, 40),
            head: main ? (main.innerText || '').replace(/\\s+/g,' ').slice(0,200) : ''});
    })()""", await_promise=False)
    try:
        return json.loads(v or '{}')
    except Exception:
        return {}


# ---------- 1. sent-count audit per subject variant ----------
SUBJECT_VARIANTS = [
    'Custom martial arts gear for',
    'HSN Warrior Apparels - club gear manufacturing for',
    'Branded uniforms & equipment for',
    'x HSN Warrior Apparels - custom club apparel',
]
print('=== SENT COUNT AUDIT (by subject variant) ===')
total_sent = 0
for sv in SUBJECT_VARIANTS:
    n = search('in:sent newer_than:1d subject:"' + sv + '"')
    print(f'  subject "{sv}" -> {n}')
    total_sent += n
print('  TOTAL by subject variants:', total_sent)

# ---------- 2. per-recipient duplicate probe ----------
rows = list(csv.DictReader(open(CSV, newline='', encoding='utf-8')))
d = {r['Lead ID']: r for r in rows}
wave = [l.strip() for l in open(WAVE) if l.strip()]
print()
print('=== PER-RECIPIENT AUDIT (in:sent to:<email>) ===')
dupes, missing, ok = [], [], 0
for lid in wave:
    r = d.get(lid)
    if not r:
        continue
    email = (r.get('Email') or '').strip().lower()
    if not email:
        continue
    n = search('in:sent newer_than:1d to:' + email)
    if n == 1:
        ok += 1
    elif n == 0:
        missing.append((lid, (r.get('Name') or '')[:28], email))
    else:
        dupes.append((lid, (r.get('Name') or '')[:28], email, n))
print(f'  exactly 1 sent: {ok} | not sent: {len(missing)} | DUPLICATES: {len(dupes)}')
for x in missing:
    print('   MISSING', x)
for x in dupes:
    print('   DUPLICATE!', x)

# ---------- 3. bounce detection ----------
print()
print('=== BOUNCE DETECTION (mailer-daemon, last 2d) ===')
br = search_rows('newer_than:2d from:mailer-daemon@google.com')
bounces = []
for it in br.get('items', []):
    if PERSONAL.search(it['from']) or AUTOMAIL.search(it['from']):
        continue
    bounces.append(it)
    print('   BOUNCE?', it['from'], '|', it['subject'][:70], '|', it['snippet'][:110])
if not bounces:
    print('   (no mailer-daemon rows visible)')
print('   head:', br.get('head', '')[:140])

# ---------- 4. client reply sweep ----------
print()
print('=== CLIENT REPLY SWEEP (Gmail, last 3d, excluding auto/system) ===')
replies = []
for q in ['newer_than:3d -from:me -from:mailer-daemon@google.com -from:postmaster '
          '-from:noreply -from:no-reply -from:notifications@google.com']:
    rr = search_rows(q)
    print(f"  [{q[:40]}] head: {rr.get('head','')[:110]}")
    for it in rr.get('items', []):
        if PERSONAL.search(it['from']) or AUTOMAIL.search(it['from']):
            continue
        replies.append(it)
        print('   * REPLY', it['from'], '|', it['subject'][:80], '|', it['snippet'][:150])
if not replies:
    print('   ZERO human client replies found')

# ---------- 5. Instagram direct inbox check ----------
print()
print('=== INSTAGRAM DM CHECK ===')
ig = [t for t in get_tabs() if 'instagram.com/direct/inbox' in t['url'] and t['type'] == 'page']
if ig:
    try:
        ws2 = connect(ig[0])
        v = js_eval(ws2, """(() => {
            const txt = document.body ? document.body.innerText : '';
            const unread = (txt.match(/unread/gi) || []).length;
            return JSON.stringify({len: txt.length, unread: unread,
                head: txt.replace(/\\s+/g,' ').slice(0, 320)});
        })()""", await_promise=False)
        ws2.close()
        print('  IG inbox:', v)
    except Exception as e:
        print('  IG probe error:', str(e)[:100])
else:
    print('  no IG inbox tab')

ws.close()
json.dump({'ok': ok, 'missing': missing, 'dupes': dupes,
           'replies': replies, 'bounces': bounces},
          open('/home/ubuntu/day14_gmail_audit.json', 'w'), indent=1)
print()
print('written /home/ubuntu/day14_gmail_audit.json')
