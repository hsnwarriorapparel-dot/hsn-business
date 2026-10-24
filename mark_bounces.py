#!/usr/bin/env python3
"""Mark bounced-email leads as FAILED in leads.csv (data-hygiene fix).

Evidence source: Gmail delivery-failure notifications (search results rows carry
the failed recipient address in the snippet). Exact email match, plus a
conservative masked-local-part pass. Atomic write, read-back verification.
"""
import sys, os, re, json, csv, time, tempfile

sys.path.insert(0, '/home/ubuntu')
import cdp_helper as ch

LEADS = '/home/ubuntu/leads.csv'
OUT = '/home/ubuntu/bounced_emails.json'
SELF = 'hsnwarriorapparel@gmail.com'
IGNORED_LOCAL = ('mailer-daemon', 'googlemail.com', 'mailer-daemon@googlemail.com')


def gather_bounce_addresses():
    """Return (exact_addresses, masked_addresses) from Gmail bounce threads."""
    tab = None
    for t in ch.get_tabs():
        if 'mail.google.com' in t.get('url', '') and t.get('type') == 'page':
            tab = t
            break
    if not tab:
        print('NO GMAIL TAB')
        return [], []

    ws = ch.connect(tab)
    ws.settimeout(45)
    try:
        search = ('from:mailer-daemon newer_than:30d '
                  '(delivery incomplete OR "address not found" '
                  'OR "couldn\'t be found" OR "unable to receive mail")')
        url = ('https://mail.google.com/mail/u/0/#search/'
               + ch_js_quote(search))
        ch.make_cdp(ws)('Page.navigate', {'url': url})
        time.sleep(14)

        rows = []
        for _ in range(4):
            expr = """(() => {
              const rows=[...document.querySelectorAll('tr')]
                .map(tr=>tr.innerText.replace(/\\s+/g,' ').trim())
                .filter(t=>t.length>30);
              return rows;
            })()"""
            out = ch.js_eval(ws, expr)
            if isinstance(out, list):
                rows = out
            ch.js_eval(ws, "(() => {const m=document.querySelector('[role=main]'); if(m) m.scrollBy(0,3000); return 1;})()")
            time.sleep(2.5)

        print('GMAIL BOUNCE ROWS:', len(rows))
        exact, masked = set(), set()
        for r in rows:
            low = r.lower()
            if not any(k in low for k in ('delivery incomplete', 'address not found',
                                          "couldn't be found", 'unable to receive mail',
                                          'delivery failed', 'mail delivery subsystem')):
                continue
            for a in re.findall(r'[A-Za-z0-9._%+\-*]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}', r):
                a = a.strip().lower()
                if not a or SELF in a:
                    continue
                if any(x in a for x in IGNORED_LOCAL):
                    continue
                if '*' in a:
                    masked.add(a)
                else:
                    exact.add(a)
        return sorted(exact), sorted(masked)
    finally:
        try:
            ws.close()
        except Exception:
            pass


def ch_js_quote(s):
    import urllib.parse
    return urllib.parse.quote(s, safe='')


def mark(bounce_exact, bounce_masked):
    with open(LEADS, encoding='utf-8', errors='replace') as f:
        rows = list(csv.reader(f))
    header = rows[0]
    idx = {h.strip(): i for i, h in enumerate(header)}
    ec, sc = idx['Email'], idx['Status']

    exact_set = {a.lower() for a in bounce_exact}
    marked, unmatched = [], []

    for r in rows[1:]:
        em = (r[ec] or '').strip().lower()
        if not em:
            continue
        if em in exact_set:
            add = ' | EMAIL FAILED (bounce confirmed 2026-10-24)'
            if 'FAILED (bounce' not in r[sc]:
                r[sc] = (r[sc] + add)[:250]
            marked.append((r[0], em))
            exact_set.discard(em)

    # conservative masked pass: u***@domain -> only if exactly ONE candidate
    for m in bounce_masked:
        mm = re.match(r'^([a-z0-9._%+\-]{1,5})\*+@([a-z0-9.\-]+)$', m)
        if not mm:
            continue
        prefix, domain = mm.groups()
        cands = [r for r in rows[1:]
                 if (r[ec] or '').strip().lower().endswith('@' + domain)
                 and (r[ec] or '').strip().lower().startswith(prefix)]
        if len(cands) == 1:
            r = cands[0]
            em = (r[ec] or '').strip().lower()
            if 'FAILED (bounce' not in r[sc]:
                r[sc] = (r[sc] + ' | EMAIL FAILED (bounce masked-match 2026-10-24)')[:250]
            marked.append((r[0], em))
            exact_set.discard(em)
        else:
            unmatched.append((m, len(cands)))

    # atomic write + row-count verify
    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(rows)
    with open(tmp, encoding='utf-8', errors='replace') as f:
        check = list(csv.reader(f))
    assert len(check) == len(rows), 'row count changed - abort'
    os.replace(tmp, LEADS)
    return marked, unmatched, len(rows) - 1


def main():
    print('=== BOUNCE MARKER START ===')
    ex, mk = gather_bounce_addresses()
    print('exact bounce addresses:', len(ex))
    print('masked bounce addresses:', len(mk))
    json.dump({'exact': ex, 'masked': mk, 'checked_at': '2026-10-24'},
              open(OUT, 'w'), indent=1)
    marked, unmatched, total = mark(ex, mk)
    print('marked leads:', len(marked))
    for lid, em in marked:
        print('  ', lid, em)
    if unmatched:
        print('ambiguous masked (skipped):', unmatched)
    print('total leads in CSV:', total)
    # read-back
    with open(LEADS, encoding='utf-8', errors='replace') as f:
        rr = list(csv.DictReader(f))
    n = sum(1 for r in rr if 'FAILED (bounce' in (r.get('Status') or ''))
    print('READ-BACK bounce marks:', n, 'rows:', len(rr))


if __name__ == '__main__':
    main()
