#!/usr/bin/env python3
"""One-shot integrity check for leads.csv + the outreach tracker.

Every reporting session re-derives the same handful of facts. Run this
instead of hand-rolling them, so the numbers in a report are measured
from disk rather than quoted from a script's own output.

    python3 scripts/verify_leads_integrity.py          # human-readable
    python3 scripts/verify_leads_integrity.py --json   # machine-readable

Exit code 0 = healthy, 1 = a check failed.
"""
import argparse
import csv
import json
import os
import re
import sys

HOME = '/home/ubuntu'
CSV_PATH = os.path.join(HOME, 'leads.csv')

# A malformed address bounces on every send. These shapes came out of
# real scrapes: a URL path prefix and URL-encoded zero-width spaces.
EMAIL_RE = re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}')


def _read_raw():
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        return list(csv.reader(f))


def _reader_rows():
    """Rows as the safe reader sees them (filtered + header skipped)."""
    sys.path.insert(0, HOME)
    import leads_safe_write as lsw
    return lsw.read_rows()


def check():
    out = {'file': CSV_PATH, 'checks': {}, 'failures': []}

    raw = _read_raw()
    disk_body = raw[1:]
    hdr = raw[0] if raw else []
    idx = {h: i for i, h in enumerate(hdr)}

    reader = _reader_rows()
    out['checks']['rows_on_disk'] = len(disk_body)
    out['checks']['rows_via_reader'] = len(reader)

    def fail(name, detail):
        out['checks'][name] = detail
        out['failures'].append('%s: %s' % (name, detail))

    # 1. header intact - if a filter ate index 0 every later read is off
    if not hdr or hdr[0] != 'Lead ID':
        fail('header', 'expected first cell "Lead ID", got %r' % (hdr[0] if hdr else None))
    else:
        out['checks']['header'] = 'OK'

    # 2. reader and disk agree - a mismatch means a row is being dropped
    if len(reader) == len(disk_body):
        out['checks']['reader_matches_disk'] = True
    else:
        fail('reader_matches_disk',
             'reader %d vs disk %d' % (len(reader), len(disk_body)))

    # 3. unique lead IDs - a duplicate makes every status write ambiguous
    ids = [r[0] for r in disk_body if r]
    dup_ids = sorted({i for i in ids if ids.count(i) > 1})
    out['checks']['duplicate_lead_ids'] = dup_ids
    if dup_ids:
        fail('duplicate_lead_ids', str(dup_ids[:10]))

    # 4. unique emails - two rows with one address means two writers raced
    emails = [(r[idx['Email']] or '').strip().lower()
              for r in disk_body if len(r) > idx.get('Email', 9)]
    emails = [e for e in emails if e]
    dup_em = sorted({e for e in emails if emails.count(e) > 1})
    out['checks']['duplicate_emails'] = len(dup_em)
    if dup_em:
        fail('duplicate_emails', str(dup_em[:10]))

    # 5. no malformed addresses - they bounce every time
    malformed = []
    for r in disk_body:
        if len(r) <= idx.get('Email', 9):
            continue
        e = (r[idx['Email']] or '').strip()
        if e and not EMAIL_RE.fullmatch(e):
            malformed.append((r[0], e[:60]))
    out['checks']['malformed_emails'] = len(malformed)
    if malformed:
        fail('malformed_emails', str(malformed[:10]))

    # 6. no placeholder rows - a test that wrote into the live tracker
    ph = [r[0] for r in disk_body
          if len(r) > 1 and 'Placeholder' in (r[1] or '')]
    out['checks']['placeholder_rows'] = len(ph)
    if ph:
        fail('placeholder_rows', str(ph[:10]))

    # 7. business counts used in every report
    buyers = [r for r in disk_body
              if len(r) > idx.get('Type', 2)
              and (r[idx['Type']] or '').startswith('Buyer company')]
    replied = [r for r in disk_body
               if len(r) > idx.get('Status', 11)
               and 'REPLIED' in (r[idx['Status']] or '')]
    out['checks']['buyer_companies'] = len(buyers)
    out['checks']['replied'] = len(replied)
    out['checks']['countries'] = len({(r[idx['Country']] or '').strip()
                                      for r in disk_body
                                      if len(r) > idx.get('Country', 6)
                                      and (r[idx['Country']] or '').strip()})

    # 8. the quota ledger - the campaign day and what it has spent
    try:
        sys.path.insert(0, HOME)
        from outreach_quota import day_tag, sent_today
        out['checks']['campaign_day'] = day_tag()
        out['checks']['cold_sent_today'] = sent_today()
        out['checks']['chain_sent_today'] = sent_today(engine='chain')
    except Exception as e:
        out['checks']['quota_error'] = str(e)

    # 9. the screened buyer pool - must be internally consistent
    try:
        sc = json.load(open(os.path.join(HOME, 'g4wb_company_screened.json')))
        buckets = ('ours', 'theirs', 'unknown')
        all_ids = [k for b in buckets for k in sc.get(b, {})]
        overlap = len(all_ids) - len(set(all_ids))
        out['checks']['screened_ours'] = len(sc.get('ours', {}))
        out['checks']['screened_theirs'] = len(sc.get('theirs', {}))
        out['checks']['screened_unknown'] = len(sc.get('unknown', {}))
        out['checks']['screened_id_overlap'] = overlap
        if overlap:
            fail('screened_id_overlap', '%d ids in 2+ buckets' % overlap)
    except Exception as e:
        out['checks']['screened_error'] = str(e)

    # 10. the reach campaign must not be retiring confirmed buyers
    try:
        st = json.load(open(os.path.join(HOME, 'company_reach_state.json')))
        proc = st.get('processed', {})
        sc = json.load(open(os.path.join(HOME, 'g4wb_company_screened.json')))
        ours = set(sc.get('ours', {}))
        retired = [k for k, v in proc.items()
                   if k in ours and isinstance(v, dict)
                   and v.get('status') == 'no-match']
        out['checks']['confirmed_buyers_retired'] = len(retired)
        if retired:
            fail('confirmed_buyers_retired', str(retired[:10]))
    except Exception as e:
        out['checks']['reach_state_error'] = str(e)

    out['ok'] = not out['failures']
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    r = check()
    if a.json:
        print(json.dumps(r, indent=2))
    else:
        c = r['checks']
        print('=== leads.csv integrity ===')
        print('  rows on disk / via reader : %d / %d' % (
            c.get('rows_on_disk', -1), c.get('rows_via_reader', -1)))
        print('  header                    : %s' % c.get('header', '?'))
        print('  duplicate lead ids        : %s' % (c.get('duplicate_lead_ids') or 'none'))
        print('  duplicate emails          : %s' % c.get('duplicate_emails', '?'))
        print('  malformed emails          : %s' % c.get('malformed_emails', '?'))
        print('  placeholder rows          : %s' % c.get('placeholder_rows', '?'))
        print('  buyer companies           : %s' % c.get('buyer_companies', '?'))
        print('  replied                   : %s' % c.get('replied', '?'))
        print('  countries                 : %s' % c.get('countries', '?'))
        print('  campaign day              : %s' % c.get('campaign_day', '?'))
        print('  cold sent today           : %s / 100' % c.get('cold_sent_today', '?'))
        print('  chain sent today          : %s' % c.get('chain_sent_today', '?'))
        print('  screened ours/theirs/unk  : %s / %s / %s' % (
            c.get('screened_ours', '?'), c.get('screened_theirs', '?'),
            c.get('screened_unknown', '?')))
        print('  screened ids in 2+buckets : %s' % c.get('screened_id_overlap', '?'))
        print('  confirmed buyers retired  : %s' % c.get('confirmed_buyers_retired', '?'))
        print()
        if r['ok']:
            print('ALL CHECKS PASS')
        else:
            print('FAILURES:')
            for f in r['failures']:
                print('  - %s' % f)
    return 0 if r['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
