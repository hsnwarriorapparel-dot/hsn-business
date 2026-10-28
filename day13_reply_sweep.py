#!/usr/bin/env python3
"""Day-13 (2026-10-27) client-reply sweep for Gmail + Instagram.

HARD RULES:
  - client replies are DRAFT-ONLY; this script NEVER sends anything
  - personal contacts (Sayyam Bhai, Shamas Ali, Afzal Bhai, Chacho Nadeem) are
    never opened or contacted
  - bounces (mailer-daemon / postmaster / self-addressed "Delivery incomplete")
    are not replies
"""
import sys, json, re, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

PERSONAL = ('sayyam', 'shamas', 'afzal', 'chacho nadeem', 'nadeem')
BOUNCE = ('mailer-daemon', 'postmaster', 'delivery status notification',
          'delivery incomplete', 'address not found', 'message blocked',
          'delivery failure', 'undeliverable', 'returned mail')
AUTO = ('go4worldbusiness', 'linkedin', 'no-reply', 'noreply',
        'facebook', 'instagram', 'notifications@', 'updates@')


def gmail_sweep():
    tabs = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
    if not tabs:
        return []
    ws = connect(tabs[0])
    cdp = make_cdp(ws)
    cdp('Page.navigate', {'url': 'https://mail.google.com/mail/u/0/#search/newer_than%3A2d%20-from%3Ame%20-is%3Aimportant'})
    time.sleep(6)
    out = []
    try:
        rows = js_eval(ws, """(() => {
            const main = document.querySelector('div[role="main"]');
            if (!main) return '[]';
            const out = [];
            for (const tr of main.querySelectorAll('tr')) {
              const t = (tr.innerText||'').trim();
              if (!t) continue;
              out.push(t.replace(/\\s+/g,' | ').slice(0,260));
            }
            return JSON.stringify(out);
        })()""", await_promise=False)
        out = json.loads(rows or '[]')
    except Exception as e:
        out = ['ERROR ' + str(e)[:80]]
    ws.close()
    return out


def ig_sweep():
    tabs = [t for t in get_tabs() if 'instagram.com/direct/inbox' in t['url'] and t['type'] == 'page']
    if not tabs:
        return []
    ws = connect(tabs[0])
    try:
        v = js_eval(ws, """(() => {
            const txt = document.body ? document.body.innerText : '';
            return txt.replace(/\\n{2,}/g,'\\n').slice(0, 2500);
        })()""", await_promise=False)
    except Exception as e:
        v = 'ERROR ' + str(e)[:80]
    ws.close()
    return [v]


if __name__ == '__main__':
    print('===== GMAIL (newer_than:2d, -from:me) =====')
    for r in gmail_sweep():
        low = r.lower()
        if any(b in low for b in BOUNCE):
            print('  [bounce] ', r[:150])
            continue
        if any(p in low for p in PERSONAL):
            print('  [PERSONAL - SKIP] ', r[:150])
            continue
        if any(a in low for a in AUTO):
            print('  [auto]   ', r[:150])
            continue
        print('  [CANDIDATE REPLY] ', r[:200])
    print()
    print('===== INSTAGRAM DIRECT INBOX =====')
    for r in ig_sweep():
        print(r[:2500])
