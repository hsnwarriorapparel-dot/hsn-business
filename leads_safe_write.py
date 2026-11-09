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
import re
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


# A lead's email must be something a buyer would REPLY to. These local
# parts are forms, privacy pages, no-reply senders and platform
# system addresses - a mail to them goes nowhere.
#
# A stale run added privacy@eximnext.com and a Wix form address
# (hash@sentry.wixpress.com) as buyer companies.
# ONLY genuinely undeliverable local parts. 'support@', 'webmaster@' and
# 'sales@' ARE real business addresses - 33 existing club leads carry
# 'support@' and have already been emailed successfully.
JUNK_EMAIL_LOCAL = re.compile(
    r'^(privacy|no-?reply|noreply|donotreply|do-not-reply|postmaster|'
    r'mailer-daemon|abuse|hostmaster|'
    r'sentry|autoreply|auto-reply)', re.I)

# Platform / form-service domains that are never a buyer.
JUNK_EMAIL_DOMAIN = re.compile(
    r'(wixpress\.com|sentry\.io|sentry\.wixpress\.com|'
    r'formsubmit\.co|formspree\.io|web3forms\.com|'
    r'googleapis\.com|amazonaws\.com|mailchimp\.com|'
    r'list-manage\.com|hubspot\.com|facebook\.com)', re.I)

# PLACEHOLDER EMAIL DOMAINS. The DOMAIN decides, never the local part:
# 'john@doe.com' is the Lorem Ipsum of emails, while
# 'john@johnaboxing.com' is a real boxing gym and 'info@my-club.it' is
# a real gym in Padova. The domain must match EXACTLY - 'my-club.it'
# contains 'my' but is a real domain.
PLACEHOLDER_EMAIL_DOMAINS = {
    'doe.com', 'doe.org', 'doe.net', 'example.com', 'example.org',
    'example.net', 'domain.com', 'email.com', 'name.com', 'test.com',
    'company.com', 'yourdomain.com', 'mydomain.com', 'yourname.com',
    'companyname.com', 'email.org', 'email.net',
}

_GENERIC_LOCAL = re.compile(
    r'^(john|jane|james|mary|foo|bar|baz|abc|xyz|test|testing|asdf|'
    r'qwerty|sample|demo|your|you|user|example|name|email|info|'
    r'contact|admin|office)@', re.I)

_GENERIC_DOMAIN = re.compile(
    r'(email|domain|name|test|company|your|my|example|site|web|mail|'
    r'host|info|sales|contact)[0-9]*'
    r'([.:\-](email|domain|name|test|company|your|my|example|site|'
    r'web|mail|host|info))?\.(com|org|net|co|io|info|biz|site|online)',
    re.I)


def is_placeholder_email(email):
    """True for an address that is obviously a template filler."""
    e = (email or '').strip().lower()
    if not e or '@' not in e:
        return False
    local, _, dom = e.partition('@')
    if dom in PLACEHOLDER_EMAIL_DOMAINS:
        return True
    if _GENERIC_LOCAL.match(e) and _GENERIC_DOMAIN.fullmatch(dom):
        return True
    return False


def email_is_contactable(email):
    """False for a form address, a no-reply sender or a privacy contact.

    Also false for a MALFORMED address. The scrape produced
    '//info@wonsbarcelona.es' and '%e2%80%a8%e2%80%a8support@sportingcluble'
    - a URL path prefix and URL-encoded zero-width spaces. Both bounce
    every time they are sent.
    """
    e = (email or '').strip().lower()
    if not e or '@' not in e:
        return False
    # a URL path or an encoded character means the scrape mangled it
    if '/' in e or '%' in e or e.startswith('mailto:') or '\\' in e:
        return False
    # the address must actually LOOK like an address
    if not re.fullmatch(r'[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}', e):
        return False
    local, dom = e.split('@', 1)
    if JUNK_EMAIL_LOCAL.match(local):
        return False
    if JUNK_EMAIL_DOMAIN.search(dom):
        return False
    if is_placeholder_email(e):
        return False
    return True


def read_rows():
    """Read leads.csv, skipping any row whose email cannot receive mail.

    The filter lives HERE, in the reader, so every caller - every funnel,
    every tracker, every writer - sees the same clean list. A row with a
    form address or a no-reply sender is invisible to the whole system,
    and write_rows() therefore never puts it back.

    The header row is always kept. Its Email cell holds the literal text
    'Email', which would otherwise be read as an address and dropped.
    """
    with open(CSV, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))
    if not rows:
        return rows
    hdr = rows[0]
    try:
        ei = hdr.index('Email')
    except ValueError:
        return rows
    clean = [hdr]
    for r in rows[1:]:
        # A row with a non-contactable email is NOT dropped - it is kept
        # with the bad address CLEARED. Dropping the row would make the
        # reader and the disk disagree, and any writer that reads and
        # writes back would silently delete the lead. The club may still
        # be reachable by phone or website.
        if len(r) > ei and (r[ei] or '').strip() \
                and not email_is_contactable(r[ei]):
            r = list(r)
            r[ei] = ''
        clean.append(r)
    return clean


def write_rows(rows):
    """Write leads.csv. Refuses to write a file without a header.

    The header row's Email cell holds the literal text 'Email'. If any
    future filter is applied without checking for the header, that row
    is read as an address and the header is deleted - which silently
    turns every later read into an off-by-one. Guard it here.
    """
    if not rows or not rows[0] or rows[0][0] != 'Lead ID':
        raise ValueError('refusing to write leads.csv without a header row '
                         '(first row was %r)' % (rows[0][:2] if rows else None))
    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(rows)
    os.replace(tmp, CSV)
    bump_generation()


def add_rows(new_rows, retries=3):
    """Append rows to leads.csv without losing anything written meanwhile.

    new_rows: list of row lists (without the header).
    Returns the new total row count.
    """
    if not new_rows:
        return len(read_rows())
    # Drop any row whose email cannot receive a reply. The check is on the
    # EMAIL COLUMN, whose index is fixed by the leads.csv header.
    try:
        with open(CSV, newline='', encoding='utf-8-sig') as f:
            _hdr = next(csv.reader(f))
        _ei = _hdr.index('Email')
        keep = []
        # 'dropped' is gone: a row with an undeliverable address is
        # CLEARED, never dropped. The old branch could never fire but it
        # printed 'dropped N row(s) with a non-contactable email', which
        # reads like leads are being lost when nothing was.
        cleared = 0
        for r in new_rows:
            # NEVER touch the header row. Its Email cell contains the
            # literal text 'Email', which the guard would read as an
            # address and DROP - deleting the header from leads.csv.
            if r and r[0] and r[0] == 'Lead ID':
                keep.append(r)
                continue
            # An EMPTY email is not a bad email - a phone-only lead is
            # legitimate and opens the WhatsApp channel. Only a NON-EMPTY
            # undeliverable address is a problem, and the fix is to CLEAR
            # the address, not to drop the row: the club is still
            # reachable by phone and website. This must match
            # read_rows(), or a reader and a writer would disagree and
            # the lead would vanish.
            if len(r) > _ei and (r[_ei] or '').strip() \
                    and not email_is_contactable(r[_ei]):
                r = list(r)
                r[_ei] = ''
                cleared += 1
            keep.append(r)
        if cleared:
            print('cleared the email on %d row(s) - the lead is kept' % cleared)
        new_rows = keep
        if not new_rows:
            return len(read_rows())
    except Exception:
        pass
    for attempt in range(retries):
        if not acquire():
            print('could not lock leads.csv - skipping %d row(s)' % len(new_rows))
            return None
        try:
            rows = read_rows()
            before = len(rows)
            # If our header differs from the file's, the file was replaced by
            # a different format - do not blindly append.
            #
            # ASSIGN THE LEAD IDs HERE, UNDER THE LOCK. A caller that
            # allocates IDs before calling add_rows() works from a snapshot
            # taken at ITS start, so a concurrent run that added rows in
            # between hands out an ID that is already taken. The stale run
            # logged 'ADDED L5286 | Muscat Sports' when L5286 was already
            # Cobra Sports and Muscat Sports was L5285.
            if new_rows and new_rows[0] and new_rows[0][0]:
                try:
                    _hdr = rows[0]
                    _ii = _hdr.index('Lead ID')
                    _used = set()
                    for r in rows[1:]:
                        if r and len(r) > _ii and r[_ii]:
                            _used.add(r[_ii].strip())
                    _next = max((int(x[1:]) for x in _used
                                 if x.startswith('L') and x[1:].isdigit()),
                                default=0)
                    for r in new_rows:
                        if len(r) > _ii and r[_ii] in _used:
                            _next += 1
                            r[_ii] = 'L%d' % _next
                            _used.add(r[_ii])
                except Exception:
                    pass
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


def update_row(lead_id, field, value, marker=None, append=False,
               prepend=False):
    """Update one lead's field in place, re-reading at write time.

    append=True APPENDS to the field instead of replacing it (used for
    the Status column, which is a ' | '-separated marker list).
    A marker that is already present is not added twice.

    prepend=True puts the value at the FRONT. THE STATUS COLUMN IS
    TRUNCATED AT 250 CHARACTERS, so a marker appended at the end can be
    cut off by a long note - and a send marker that is cut off is
    invisible, which means the next wave emails the same lead again.
    Three buyer companies were sent twice on 2026-11-08 for exactly
    that reason. The send marker must go at the front.
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
                        if prepend:
                            cur = (r[fi] or '').strip(' |')
                            if value and value not in cur.split(' | '):
                                r[fi] = (value + (' | ' + cur if cur else ''))[:250]
                        elif append:
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

def guarded_write_csv(rows, path=None, read_gen=None):
    # Resolve the path AT CALL TIME. `path=CSV` as a default argument
    # captures the value at import, so a test that sets `lsw.CSV = TMP`
    # was ignored and the test wrote into the REAL leads.csv - which is
    # how six 'Placeholder Test Club' rows got into the tracker.
    if path is None:
        path = CSV
    """Write the WHOLE file, but refuse if leads.csv changed underneath us.

    A stale process (one that started before this module existed) has an
    old in-memory copy. If the generation counter moved since it read the
    file, its copy is out of date and writing it would destroy newer work.
    The write is refused instead.
    """
    if read_gen is None:
        read_gen = current_generation()
    if generation_is_stale(read_gen):
        print('REFUSING a stale leads.csv write (generation moved %s -> %s) - '
              'the in-memory copy is out of date'
              % (read_gen, current_generation()))
        return False
    write_rows(rows)
    return True


def safe_write_csv(rows, path=None, expect_gen=None):
    # Resolve the path AT CALL TIME - see guarded_write_csv for why.
    if path is None:
        path = CSV
    """Atomically write rows to a CSV, holding the shared lock.

    Every live writer goes through this so two processes can never write
    leads.csv at the same time. The lock is taken BEFORE the write and
    released after the atomic rename.

    expect_gen: the generation the caller read. If the generation moved since
    then, the caller's copy is stale and the write is REFUSED - that is what
    stops a process that started before this module existed from clobbering
    newer work. Pass None to skip the check (the caller re-read under the
    lock anyway).
    """
    acquire()
    try:
        if expect_gen is not None and generation_is_stale(expect_gen):
            print('REFUSING a stale leads.csv write (generation moved %s -> %s) - '
                  'the in-memory copy is out of date'
                  % (expect_gen, current_generation()))
            return False
        # SELF-HEALING STALE CHECK (no call-site changes needed): if the
        # caller's copy is MISSING rows that the live file has, the caller
        # read the file before someone else wrote to it. Writing the stale
        # copy would destroy that newer work - so MERGE instead: keep the
        # live file's rows and add any of the caller's rows that are not
        # already there.
        if path == CSV:
            try:
                live = read_rows()
                if len(live) > len(rows):
                    live_ids = set(r[0] for r in live[1:] if r)
                    have = set(r[0] for r in rows[1:] if r)
                    missing = live_ids - have
                    if missing:
                        extra = [r for r in live[1:] if r and r[0] in missing]
                        print('STALE COPY DETECTED - %d newer row(s) would have been '
                              'lost; merging them in instead' % len(extra))
                        merged = list(rows)
                        seen = set(r[0] for r in merged[1:] if r)
                        for r in extra:
                            if r[0] not in seen:
                                merged.append(r)
                                seen.add(r[0])
                        rows = merged
            except Exception:
                pass
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or '.', suffix='.csv.tmp')
        with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerows(rows)
        os.replace(tmp, path)
        bump_generation()
        return True
    finally:
        release()

# ------------------------------------------------------------ generation ----
# A process that started BEFORE the safe writer existed still has the old
# read-once/write-whole-file code in memory. It can still clobber the file.
#
# This guard catches that: leads.csv's generation is tracked in a side file.
# A writer records the generation it read; if the generation changed before
# it wrote, its copy is stale and the write is REFUSED. The safe writer
# bumps the generation on every write.
GEN = '/home/ubuntu/leads.csv.generation'


def current_generation():
    try:
        return int(open(GEN).read().strip() or 0)
    except Exception:
        return 0


def bump_generation():
    g = current_generation() + 1
    try:
        with open(GEN, 'w') as f:
            f.write(str(g))
    except Exception:
        pass
    return g


def generation_is_stale(read_gen):
    """True if leads.csv changed since the caller read it."""
    return current_generation() != read_gen
