#!/usr/bin/env python3
"""Canonical campaign counters for HSN — one definition used by every report.
Counts a channel as DONE only when the status carries an explicit completion
marker for that channel (never a 'not found' / 'failed' / 'skipped' marker)."""
import csv
import os
import re

CSV = '/home/ubuntu/leads.csv'
# Day tag used for the "today" block below. Auto-detected as the most recent
# calendar date present in any Status (was hardcoded and went stale daily).
# Override with the HSN_TODAY_TAG env var if a manual re-run needs a fixed day.
TODAY_TAG = os.environ.get('HSN_TODAY_TAG') or None


def _detect_today_tag():
    """Most recent YYYY-MM-DD date stamped in any row's Status."""
    global TODAY_TAG
    if TODAY_TAG:
        return TODAY_TAG
    found = set()
    for r in rows[1:]:
        for m in re.findall(r'20\d\d-\d\d-\d\d', g(r, 'Status') or ''):
            found.add(m)
    TODAY_TAG = max(found) if found else ''
    return TODAY_TAG


def marker_today(r, *needles):
    """Return the Status marker that carries TODAY_TAG AND one of the needles.

    WHY (2026-11-02): the naive "row contains today's date AND contains
    'email sent'" test counts a lead that was emailed on Day-18 but received an
    IG marker today as an email sent today, and a row whose only 'wa sent'
    marker is from Day 9 but which got an IG marker today as a WA sent today.
    Both inflated the Day-19 report (55 emails / 1 WA vs the true 50 / 0).
    Markers are ' | '-separated, so the day tag must live in the SAME marker
    as the completion token.
    """
    tag = _detect_today_tag()
    if not tag:
        return None
    for part in (g(r, 'Status') or '').split('|'):
        p = part.strip()
        if tag not in p:
            continue
        low = p.lower()
        if any(n.lower() in low for n in needles):
            return p
    return None

# IG done: an explicit follow/DM completion token
IG_DONE_PAT = re.compile(r'(ig follow=(ok|clicked|no-btn))|(dm=sent)|(ig followed)|(ig dm sent)', re.I)
# WA done: an explicit send confirmation
WA_DONE_PAT = re.compile(r'(whatsapp sent)|(\bwa sent\b)|(wa sent \(verified)', re.I)
EMAIL_DONE_PAT = re.compile(r'email sent', re.I)
FAIL_PAT = re.compile(r'email failed|wa failed|ig err|recipient-not-registered', re.I)

rows = list(csv.reader(open(CSV, encoding='utf-8-sig', errors='replace')))
hdr = rows[0]
H = {h: i for i, h in enumerate(hdr)}


def g(r, k):
    i = H.get(k)
    return r[i] if i is not None and i < len(r) else ''


def email_ok(r):
    sl = g(r, 'Status')
    return bool(EMAIL_DONE_PAT.search(sl))


def ig_ok(r):
    sl = g(r, 'Status')
    if FAIL_PAT.search(sl) and not IG_DONE_PAT.search(sl):
        return False
    return bool(IG_DONE_PAT.search(sl))


def wa_ok(r):
    sl = g(r, 'Status')
    if 'not on whatsapp' in sl.lower() or "isn't on whatsapp" in sl.lower():
        return False
    return bool(WA_DONE_PAT.search(sl))


def hot(r):
    return 'HOT' in g(r, 'Status').upper()


def count(fn):
    return sum(1 for r in rows[1:] if fn(r))


if __name__ == '__main__':
    total = len(rows) - 1
    print("total leads:", total)
    print("emails sent:", count(email_ok))
    print("IG follow+DM done:", count(ig_ok))
    print("WhatsApp sent:", count(wa_ok))
    print("HOT leads:", count(hot))
    print("with email:", sum(1 for r in rows[1:] if g(r, 'Email').strip()))
    print("with phone:", sum(1 for r in rows[1:] if g(r, 'Phone').strip()))
    print("failed rows:", sum(1 for r in rows[1:] if 'failed' in g(r, 'Status').lower()))
    print("excluded rows:", sum(1 for r in rows[1:] if 'excluded' in g(r, 'Status').lower()))
    today = [r for r in rows[1:] if _detect_today_tag() in g(r, 'Status')]
    print("--- today", TODAY_TAG, "---")
    print("rows touched:", len(today))
    # per-channel "today" counts must come from a SINGLE marker that carries
    # today's date AND that channel's completion token (see marker_today).
    print("emails sent today:", sum(1 for r in today
                                     if marker_today(r, 'email sent')))
    print("IG done today:", sum(1 for r in today
                                if marker_today(r, 'ig follow=', 'dm=sent',
                                                'ig followed', 'ig dm sent')))
    print("WA sent today:", sum(1 for r in today
                                if marker_today(r, 'whatsapp sent', 'wa sent')))
    from collections import Counter
    print("countries:", dict(Counter(g(r, 'Country') or '?'
                                     for r in today
                                     if marker_today(r, 'email sent'))))
