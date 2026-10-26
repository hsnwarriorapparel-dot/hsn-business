#!/usr/bin/env python3
"""Inspect specific rows' raw cells + find rows whose Name field is malformed
(a stray trailing letter after a newline, etc.) so the email greeting is clean."""
import csv, re, sys

CSV = '/home/ubuntu/leads.csv'
rows = list(csv.reader(open(CSV, encoding='utf-8', errors='replace')))
idx = {h: i for i, h in enumerate(rows[0])}
targets = sys.argv[1:] if len(sys.argv) > 1 else []
for r in rows[1:]:
    if targets and r[0] not in targets:
        continue
    print("===", r[0], "===")
    for h in ('Name', 'Type', 'IG Username', 'City', 'Country', 'Phone', 'Email', 'Website', 'Status'):
        i = idx[h]
        print(f"  {h:14}: {repr(r[i]) if i < len(r) else 'MISSING'}")
print()
print("=== rows whose Name contains a newline or trailing single-letter token ===")
n = 0
for r in rows[1:]:
    i = idx['Name']
    nm = r[i] if i < len(r) else ''
    if '\n' in nm or re.search(r'\s[A-Z]$', nm.strip()):
        n += 1
        if n <= 25:
            print("  ", r[0], repr(nm[:60]))
print("  total:", n)
print()
print("=== rows whose Email starts with '-' or '+' ===")
for r in rows[1:]:
    i = idx['Email']
    e = (r[i] if i < len(r) else '').strip()
    if e.startswith('-') or e.startswith('+'):
        print("  ", r[0], repr(e[:50]))
