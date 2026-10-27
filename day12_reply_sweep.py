#!/usr/bin/env python3
"""Day-12 (2026-10-26) reply sweep: Gmail inbox + WhatsApp chats.

READ-ONLY for any reply: this NEVER sends. Client replies are draft-only
until the user says "send". Personal contacts are filtered out entirely.
"""
import sys, time, json, re
from urllib.parse import quote
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

PERSONAL = re.compile(r'sayyam|shamas|afzal|chacho|bhai', re.I)
AUTOMAIL = re.compile(r'mailer-daemon|postmaster|mail-daemon|noreply|no-reply|'
                      r'notifications@google|support@|bounce|mailer@', re.I)

JS = r"""(() => {
  const spans = Array.from(document.querySelectorAll('span[email]'));
  const seen = new Set();
  const out = [];
  for (const s of spans) {
    const from = s.getAttribute('email') || '';
    if (!from || seen.has(from)) continue;
    seen.add(from);
    let row = s.closest('div[role="listitem"]') || s.closest('div.adn.ads') ||
              s.closest('tr') || s.closest('div');
    const txt = row ? (row.innerText || '').replace(/\s+/g, ' ').trim() : '';
    const subjEl = row ? row.querySelector('span[data-thread-subject]') : null;
    const subject = subjEl ? (subjEl.innerText || '') : '';
    out.push({from: from, subject: subject.slice(0, 140), snippet: txt.slice(0, 300)});
  }
  const main = document.querySelector('div[role="main"]');
  return JSON.stringify({spans: spans.length, items: out.slice(0, 40),
    mainHead: main ? (main.innerText || '').replace(/\s+/g,' ').slice(0, 200) : ''});
})()"""

print('=== GMAIL SWEEP ===')
gm = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
if not gm:
    print('  no gmail tab')
else:
    ws = connect(gm[0])
    cdp = make_cdp(ws)
    cdp('Page.enable')
    cdp('Page.bringToFront')
    time.sleep(1)
    out_all = []
    for q in ["newer_than:2d -from:me -from:mailer-daemon@google.com -from:postmaster -from:noreply",
              "newer_than:7d -from:me -from:mailer-daemon@google.com -from:postmaster -from:noreply"]:
        cdp('Page.navigate', {'url': 'https://mail.google.com/mail/u/0/#search/' + quote(q)})
        time.sleep(7)
        v = js_eval(ws, JS, await_promise=False)
        try:
            d = json.loads(v)
        except Exception:
            print('  PARSE FAIL', str(v)[:150])
            continue
        print(f"  [{q[:34]}] spans={d.get('spans')} | {d.get('mainHead','')[:90]}")
        for it in d.get('items', []):
            if PERSONAL.search(it['from']) or AUTOMAIL.search(it['from']):
                continue
            it['query'] = q
            out_all.append(it)
    seen = set()
    uniq = []
    for it in out_all:
        k = (it['from'], it['subject'])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(it)
    print('  candidate business replies:', len(uniq))
    for it in uniq:
        print('   *', it['from'], '|', it['subject'][:80], '|', it['snippet'][:150])
    ws.close()

print('=== WHATSAPP SWEEP ===')
wa = [t for t in get_tabs() if 'web.whatsapp' in t['url'] and t['type'] == 'page']
if not wa:
    print('  no WA tab')
else:
    try:
        ws = connect(wa[0])
        v = js_eval(ws, """(() => {
          const txt = document.body ? document.body.innerText : '';
          return JSON.stringify({qr: /Scan to log in/i.test(txt),
            pane: !!document.querySelector('#pane-side'),
            head: txt.replace(/\\s+/g,' ').slice(0, 250)});
        })()""", await_promise=False)
        ws.close()
        d = json.loads(v)
        if d.get('qr'):
            print('  WA SESSION DEAD (QR screen) - no reply sweep possible, user must re-link')
        else:
            print('  WA pane present:', d.get('head', '')[:200])
    except Exception as e:
        print('  WA probe error:', str(e)[:120])
