#!/usr/bin/env python3
"""Verify the 20 unsent wave leads are still unsent in leads.csv (no loss, no duplicate risk)."""
import csv, os, subprocess, sys

def g(r, k):
    for key in r:
        if key and key.strip().lower() == k.lower():
            return r[k] or ""
    return ""

ROWS = {g(r, "Lead ID"): r for r in csv.DictReader(open("/home/ubuntu/leads.csv"))}
wave = [l.strip() for l in open("/home/ubuntu/day16_wave.txt") if l.strip()]
sent, unsent = [], []
for lid in wave:
    r = ROWS.get(lid)
    if not r:
        continue
    (sent if "email sent" in g(r, "Status").lower() else unsent).append(
        (lid, g(r, "Name"), g(r, "Email"), g(r, "Country"), g(r, "Status")[:60]))
print(f"WAVE FILE LEADS: {len(wave)} | marked email sent: {len(sent)} | STILL UNSENT: {len(unsent)}")
print("\n--- UNSENT (will be picked up by next wave, no duplicate) ---")
for u in unsent:
    print(" ", u[0], "|", u[1][:34], "|", u[2][:38], "|", u[3], "|", u[4])
missing = [l for l in wave if l not in ROWS]
print("\nWAVE IDS NOT IN CSV:", missing[:10], "count", len(missing))

# Are those unsent still valid ammo per the wave-builder filter?
def valid_email(e):
    e = e.strip().lower()
    return "@" in e and "." in e.split("@")[-1] and not any(x in e for x in
           ("example.com", "domain.com", "dominio.com", "mysite.com", "2x.jpg", "2x.png"))
ammo = []
for r in ROWS.values():
    s = g(r, "Status").lower()
    if not valid_email(g(r, "Email")):
        continue
    if "email sent" in s or "excluded" in s or "failed" in s or "re-hunt" in s:
        continue
    ammo.append(r)
print("\nTOTAL AMMO NOW (valid email, no marker):", len(ammo))
from collections import Counter
print("by country:", dict(Counter(g(r, "Country") or "?" for r in ammo).most_common(10)))
print("\nUNSENT-of-wave also in ammo?", all(any(g(r,'Lead ID')==u[0] for r in ammo) for u in unsent))
