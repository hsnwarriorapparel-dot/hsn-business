#!/usr/bin/env python3
"""Canonical campaign counters for HSN — one definition used by every report.
Counts a channel as DONE only when the status carries an explicit completion
marker for that channel (never a 'not found' / 'failed' / 'skipped' marker)."""
import csv
import re

CSV = '/home/ubuntu/leads.csv'
# Day tag used for the "today" block below; keep it in sync with the daily run.
TODAY_TAG = '2026-10-26'

# IG done: an explicit follow/DM completion token
IG_DONE_PAT = re.compile(r'(ig follow=(ok|clicked|no-btn))|(dm=sent)|(ig followed)|(ig dm sent)', re.I)
# WA done: an explicit send confirmation
WA_DONE_PAT = re.compile(r'(whatsapp sent)|(\bwa sent\b)|(wa sent \(verified)', re.I)
EMAIL_DONE_PAT = re.compile(r'email sent', re.I)
FAIL_PAT = re.compile(r'email failed|wa failed|ig err|recipient-not-registered', re.I)

rows = list(csv.reader(open(CSV, encoding='utf-8', errors='replace')))
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
    today = [r for r in rows[1:] if TODAY_TAG in g(r, 'Status')]
    print("--- today", TODAY_TAG, "---")
    print("rows touched:", len(today))
    print("emails sent today:", sum(1 for r in today if email_ok(r)))
    print("IG done today:", sum(1 for r in today if ig_ok(r)))
    print("WA sent today:", sum(1 for r in today if wa_ok(r)))
    from collections import Counter
    print("countries:", dict(Counter(g(r, 'Country') or '?' for r in today if email_ok(r))))
