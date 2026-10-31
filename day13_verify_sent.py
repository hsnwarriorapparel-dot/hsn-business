#!/usr/bin/env python3
"""Independent Gmail Sent verification for the Day-13 wave.

The CSV says what we MARKED; this checks what Gmail actually has. Per the
Day-12 gotcha, `in:sent newer_than:1d` with no subject filter shows no count,
so each of the 4 subject variants is queried separately and the "of N
Conversations" header is parsed. A duplicate probe (`to:<email>`) runs over a
sample of recipients.
"""
import sys, json, time, csv, re
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

CSV = '/home/ubuntu/leads.csv'
WAVE = '/home/ubuntu/day13_wave.txt'

SUBJECTS = [
    # common fragments of the 4 subject templates (the {name} slot is
    # substituted per lead, so search a literal common fragment instead)
    "Custom martial arts gear for",
    "club gear manufacturing for",
    "Branded uniforms & equipment for",
    "custom club apparel",
]


def main():
    tabs = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
    if not tabs:
        print('NO GMAIL TAB')
        return
    ws = connect(tabs[0])
    cdp = make_cdp(ws)

    def search(q):
        url = ('https://mail.google.com/mail/u/0/#search/' +
               __import__('urllib.parse', fromlist=['quote']).quote(q))
        cdp('Page.navigate', {'url': url})
        time.sleep(5)
        v = js_eval(ws, """(() => {
            const main = document.querySelector('div[role="main"]');
            const txt = main ? main.innerText : '';
            const m = txt.match(/(\\d+)\\s*[–-]\\s*\\d+\\s+of\\s+(\\d+)/);
            return JSON.stringify({count: m ? m[2] : null, head: txt.replace(/\\s+/g,' ').slice(0,180)});
        })()""", await_promise=False)
        return json.loads(v or '{}')

    print('--- per-subject conversation counts (in:sent newer_than:1d) ---')
    total = 0
    for s in SUBJECTS:
        r = search('in:sent newer_than:1d subject:"' + s + '"')
        n = int(r.get('count') or 0)
        total += n
        print(f"  {n:>4}  |  {s[:56]}")
    print('  TOTAL sent conversations by subject:', total)

    print()
    print('--- duplicate probe (to:<email>, expect 1 each) ---')
    rows = list(csv.DictReader(open(CSV, newline='', encoding='utf-8-sig')))
    marked = [r for r in rows if 'email sent (Daily 2026-10-27)' in (r.get('Status') or '')]
    print('  CSV-marked as sent today:', len(marked))
    sample = marked[:8] + marked[-4:] if len(marked) > 12 else marked
    dups = 0
    for r in sample:
        q = 'in:sent newer_than:1d to:' + (r.get('Email') or '').strip().lower()
        res = search(q)
        n = int(res.get('count') or 0)
        flag = 'OK' if n == 1 else ('DUP!' if n > 1 else 'NOT-FOUND')
        if n != 1:
            dups += 1
        print(f"  {flag:10} {r['Lead ID']} {r.get('Email','')[:38]} -> {n}")
    print('  duplicate/suspect recipients in sample:', dups)
    ws.close()


if __name__ == '__main__':
    main()
