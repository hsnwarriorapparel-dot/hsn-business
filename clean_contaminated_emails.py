#!/usr/bin/env python3
"""Scrape-contamination cleanup: mark rows whose Email cell holds an image
filename / concatenated junk instead of a real address, so no future wave can
pick them up. Idempotent. Verifies by read-back.
"""
import csv, os, re, tempfile, sys

LEADS = '/home/ubuntu/leads.csv'

BAD_PAT = re.compile(
    r'@\S+\.(jpe?g|png|gif|webp|svg|pdf|html?|php)$', re.I)


def looks_contaminated(em: str) -> bool:
    e = (em or '').strip()
    if not e:
        return False
    low = e.lower()
    if BAD_PAT.search(low):
        return True
    # known junk local parts / suffixes seen in scraped pages
    junk_locals = {
        'voorbeeld@email.nl', 'your@email.com', 'you@email.com',
        'esempio@ilmiosito.com', 'contatto@esempio.it',
    }
    if low in junk_locals:
        return True
    # concatenated-two-addresses pattern (two @ in the cell)
    if low.count('@') > 1:
        return True
    # trailing junk glued to a valid-looking domain
    if re.search(r'\.(com|net|org|it|es|de|nl|uk|pt|fr|ie)[a-z]{2,}$', low):
        return True
    return False


def main():
    with open(LEADS, encoding='utf-8-sig', errors='replace') as f:
        rows = list(csv.reader(f))
    idx = {h.strip(): i for i, h in enumerate(rows[0])}
    ec, sc = idx['Email'], idx['Status']

    changed = []
    for r in rows[1:]:
        em = (r[ec] or '').strip()
        if not em:
            continue
        if not looks_contaminated(em):
            continue
        status = r[sc] or ''
        if 'EXCLUDED (scrape contamination' not in status:
            r[sc] = (status + ' | EXCLUDED (scrape contamination: email cell is not a valid address) ')[:250]
            changed.append((r[0], em))

    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(rows)
    with open(tmp, encoding='utf-8', errors='replace') as f:
        check = list(csv.reader(f))
    assert len(check) == len(rows), 'row count changed - abort'
    os.replace(tmp, LEADS)

    print('contamination rows marked:', len(changed))
    for lid, em in changed:
        print('  ', lid, em)

    # read-back verification
    with open(LEADS, encoding='utf-8-sig', errors='replace') as f:
        rr = list(csv.DictReader(f))
    n = sum(1 for r in rr if 'EXCLUDED (scrape contamination' in (r.get('Status') or ''))
    print('READ-BACK: contamination-excluded =', n, '| total rows =', len(rr))
    leftover = [(r['Lead ID'], r['Email']) for r in rr
                if (r.get('Email') or '').strip()
                and looks_contaminated(r['Email'])
                and 'EXCLUDED (scrape contamination' not in (r.get('Status') or '')]
    print('READ-BACK: contaminated but NOT excluded =', leftover)


if __name__ == '__main__':
    main()
