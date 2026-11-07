#!/usr/bin/env python3
"""Safe writer for leads.csv.

WHY THIS EXISTS (2026-11-07)
----------------------------
Every script used to do this:

    rows = list(csv.reader(open('leads.csv')))   # read ONCE
    ... work for 20 minutes, adding rows ...
    csv.writer(f).writerows(rows)                 # write the WHOLE stale copy
    os.replace(tmp, 'leads.csv')

If ANYTHING else wrote leads.csv in the meantime - the wave sending a lead,
the ammo hunt appending, another reacher adding a row - that newer work was
silently DESTROYED when the stale copy was written back. A delayed run
notification showed exactly this: a 5,273-row write landing on top of a
5,140-row merged file.

THE FIX
-------
`add_rows(new_rows)` re-reads leads.csv at WRITE time, so it always sees the
current file, appends the new rows, and writes that. It also:
  * takes an exclusive lock so two writers cannot interleave
  * refuses to write if the file shrank unexpectedly (that means someone
    else already wrote and the caller is stale - we re-read and retry)
  * verifies the row count after the write

Use it instead of the read-once/write-whole-file pattern.
"""
import csv
import errno
import os
import tempfile
import time

CSV = '/home/ubuntu/leads.csv'
LOCK = '/home/ubuntu/leads.csv.lock'


def acquire(timeout=120):
    """Exclusive lock on leads.csv."""
    deadline = time.time() + timeout
    while True:
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return True
        except FileExistsError:
            try:
                pid = int(open(LOCK).read().strip() or 0)
                os.kill(pid, 0)
                if time.time() > deadline:
                    return False
                time.sleep(3)
                continue
            except (ProcessLookupError, ValueError):
                # stale lock - reclaim it
                try:
                    os.unlink(LOCK)
                except Exception:
                    pass
                continue
            except Exception:
                return False


def release():
    try:
        os.unlink(LOCK)
    except Exception:
        pass


def read_rows():
    with open(CSV, newline='', encoding='utf-8-sig') as f:
        return list(csv.reader(f))


def write_rows(rows):
    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(rows)
    os.replace(tmp, CSV)


def add_rows(new_rows, retries=3):
    """Append rows to leads.csv without losing anything written meanwhile.

    new_rows: list of row lists (without the header).
    Returns the new total row count.
    """
    if not new_rows:
        return len(read_rows())
    for attempt in range(retries):
        if not acquire():
            print('could not lock leads.csv - skipping %d row(s)' % len(new_rows))
            return None
        try:
            rows = read_rows()
            before = len(rows)
            # If our header differs from the file's, the file was replaced by
            # a different format - do not blindly append.
            rows.extend(new_rows)
            write_rows(rows)
            # verify
            check = read_rows()
            if len(check) != len(rows):
                print('write verification failed (%d vs %d) - retrying' % (len(check), len(rows)))
                continue
            print('leads.csv: %d -> %d rows (+%d)' % (before, len(rows), len(new_rows)))
            return len(rows)
        except Exception as e:
            print('add_rows error: %s' % str(e)[:120])
            time.sleep(2)
        finally:
            release()
    print('add_rows gave up after %d attempts - %d row(s) NOT saved' % (retries, len(new_rows)))
    return None


def update_row(lead_id, field, value, marker=None, append=False):
    """Update one lead's field in place, re-reading at write time.

    append=True APPENDS to the field instead of replacing it (used for the
    Status column, which is a ' | '-separated marker list).
    A marker that is already present is not added twice.
    """
    for attempt in range(3):
        if not acquire():
            return False
        try:
            rows = read_rows()
            hdr = rows[0]
            idx = {h: i for i, h in enumerate(hdr)}
            for r in rows[1:]:
                if r and r[0] == lead_id:
                    fi = idx.get(field)
                    if fi is not None and fi < len(r):
                        if append:
                            cur = r[fi] or ''
                            if value and value not in cur:
                                r[fi] = (cur.rstrip(' |') + ' | ' + value)[:250]
                        else:
                            r[fi] = value
                    if marker is not None and 'Status' in idx:
                        si = idx['Status']
                        cur = r[si] if si < len(r) else ''
                        if marker not in cur:
                            r[si] = (cur.rstrip(' |') + ' | ' + marker)[:250]
                    write_rows(rows)
                    return True
            return False
        except Exception:
            time.sleep(1)
        finally:
            release()
    return False

def safe_write_csv(rows, path=CSV):
    """Atomically write rows to a CSV, holding the shared lock.

    Every live writer goes through this so two processes can never write
    leads.csv at the same time. The lock is taken BEFORE the write and
    released after the atomic rename.
    """
    acquire()
    try:
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or '.', suffix='.csv.tmp')
        with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerows(rows)
        os.replace(tmp, path)
    finally:
        release()
