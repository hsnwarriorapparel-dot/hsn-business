#!/usr/bin/env python3
"""Row-targeted email/notes update for leads.csv (safe: re-reads disk, updates
only the named row, atomic replace, then reads back to verify)."""
import csv, os, sys, tempfile

CSV = '/home/ubuntu/leads.csv'


def update(lead_id, email=None, notes=None, append_status=None):
    with open(CSV, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))
    hdr = rows[0]
    idx = {h: i for i, h in enumerate(hdr)}
    found = False
    for r in rows[1:]:
        if r and r[0] == lead_id:
            found = True
            if email is not None:
                r[idx['Email']] = email
            if notes is not None:
                r[idx['Notes']] = (r[idx['Notes']] if idx['Notes'] < len(r) else '') + (' | ' if r[idx['Notes']] else '') + notes
            if append_status is not None:
                cur = (r[idx['Status']] if idx['Status'] < len(r) else '') or ''
                r[idx['Status']] = (cur.rstrip(' |') + ' | ' + append_status)[:250]
            break
    if not found:
        print('NOT FOUND:', lead_id)
        return False
    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(rows)
    os.replace(tmp, CSV)
    # READ BACK
    with open(CSV, newline='', encoding='utf-8-sig') as f:
        back = list(csv.reader(f))
    for r in back[1:]:
        if r and r[0] == lead_id:
            print('VERIFIED %s: email=%r notes=%r' % (lead_id, r[idx['Email']], (r[idx['Notes']] or '')[:120]))
            return True
    print('READBACK FAILED')
    return False


if __name__ == '__main__':
    lid = sys.argv[1]
    em = sys.argv[sys.argv.index('--email') + 1] if '--email' in sys.argv else None
    nt = sys.argv[sys.argv.index('--notes') + 1] if '--notes' in sys.argv else None
    st = sys.argv[sys.argv.index('--status') + 1] if '--status' in sys.argv else None
    ok = update(lid, em, nt, st)
    sys.exit(0 if ok else 1)
