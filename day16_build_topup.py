#!/usr/bin/env python3
"""Build a TOP-UP wave file containing ONLY leads from day16_wave.txt that are
still unsent (no 'email sent' marker, no FAILED/EXCLUDED). Re-running this is
safe: it never includes an already-sent lead, so no duplicate sends.
"""
import csv, sys

CSV = '/home/ubuntu/leads.csv'
SRC = '/home/ubuntu/day16_wave.txt'
OUT = '/home/ubuntu/day16_topup_wave.txt'

def g(r, k):
    for key in r:
        if key and key.strip().lower() == k.lower():
            return r[key] or ""
    return ""

rows = {g(r, "Lead ID"): r for r in csv.DictReader(open(CSV, encoding='utf-8-sig'))}
src = [l.strip() for l in open(SRC) if l.strip()]

out, skipped_sent, skipped_bad = [], 0, 0
for lid in src:
    r = rows.get(lid)
    if not r:
        continue
    s = g(r, "Status").lower()
    e = g(r, "Email").strip().lower()
    if "email sent" in s:
        skipped_sent += 1
        continue
    if "excluded" in s or "re-hunt" in s:
        skipped_bad += 1
        continue
    if not e or "@" not in e or "." not in e.split("@")[-1]:
        skipped_bad += 1
        continue
    out.append(lid)

with open(OUT, 'w') as f:
    f.write("\n".join(out) + ("\n" if out else ""))

print(f"src wave: {len(src)} | already sent (skip): {skipped_sent} | excluded/bad (skip): {skipped_bad}")
print(f"TOP-UP WAVE: {len(out)} leads -> {OUT}")
for lid in out:
    r = rows[lid]
    print("  ", lid, "|", g(r, "Name")[:32], "|", g(r, "Email")[:36], "|", g(r, "Country"))
