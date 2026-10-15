#!/usr/bin/env python3
"""SAFE CSV updater: writes temp -> verifies -> atomic rename. Never truncates the original."""
import csv, sys, os, tempfile

CSV = '/home/ubuntu/leads.csv'

def safe_update(lead_id, new_status=None, new_notes=None, append_status=None):
    with open(CSV) as f:
        rows = list(csv.reader(f))
    if not rows or not rows[0]:
        print("ERROR: source CSV empty - refusing to touch")
        sys.exit(1)
    idx = {h: i for i, h in enumerate(rows[0])}
    changed = False
    for r in rows[1:]:
        if r[0] == lead_id:
            if new_status:
                r[idx['Status']] = new_status
            if append_status:
                r[idx['Status']] = (r[idx['Status']] + ' | ' + append_status)[:250]
            if new_notes:
                r[idx['Notes']] = new_notes
            changed = True
    if not changed:
        print(f"WARNING: {lead_id} not found")
        return False
    # write to temp, verify, atomic move
    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='') as f:
        csv.writer(f).writerows(rows)
    # verify temp
    with open(tmp) as f:
        check = list(csv.reader(f))
    assert len(check) == len(rows), 'row count mismatch'
    os.replace(tmp, CSV)
    print(f"OK: {lead_id} updated ({len(rows)-1} leads intact)")
    return True

if __name__ == '__main__':
    # usage: safe_csv_update.py L132 --status "..." --notes "..."
    lid = sys.argv[1]
    status = notes = None
    if '--status' in sys.argv:
        status = sys.argv[sys.argv.index('--status') + 1]
    if '--notes' in sys.argv:
        notes = sys.argv[sys.argv.index('--notes') + 1]
    safe_update(lid, status, notes)
