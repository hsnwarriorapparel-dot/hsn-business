#!/usr/bin/env python3
"""Ammo top-up for the 2026-10-28 wave (Day 14).

Ammo check at 2026-10-28 00:30 UTC: only 64 clean leads with an email -> below
the 100/day quota. Runs the proven gmaps_daily_scrape functions for FOUR USA
cities not scraped in the last 3 days, then appends deduped leads, rebuilds the
tracker and commits+pushes.

Recently scraped (skip): Madrid/Barcelona (10-24), Rome/Zurich/Lisbon/Milan
(10-25), Zurich/Lisbon/Manchester/Dublin/Paris/Amsterdam (10-26),
Chicago/Houston/Berlin (10-27).
"""
import sys, datetime, importlib.util

spec = importlib.util.spec_from_file_location("gmaps_daily_scrape", "/home/ubuntu/gmaps_daily_scrape.py")
gm = importlib.util.module_from_spec(spec)
sys.modules["gmaps_daily_scrape"] = gm
spec.loader.exec_module(gm)

gm.DATE = "2026-10-28-ammo-topup"

# Pick by NAME (indexing past 23 raises IndexError; the pool has 24 entries).
# These four USA cities were NOT scraped in the last 3 days.
WANTED = ["Phoenix AZ", "Philadelphia PA", "San Antonio TX", "Atlanta GA"]
PICKS = [c for c in gm.CITIES if c[0] in WANTED]
assert len(PICKS) == len(WANTED), f"city lookup failed: got {[p[0] for p in PICKS]}"

gm.log("=== GMAPS AMMO TOP-UP START (Day 14, cities: %s) ===" % ", ".join(p[0] for p in PICKS))
gm.ensure_engine()

all_leads = []
for city, lat, lon, country, prefix in PICKS:
    leads = gm.run_city(city, lat, lon, country, prefix)
    no_email = [l for l in leads if not l["email"] and l["website"]]
    gm.log(f"{city}: enriching {len(no_email)} websites for emails")
    for l in no_email:
        gm.enrich_website(l)
    got = sum(1 for l in leads if l["email"])
    gm.log(f"{city}: {got}/{len(leads)} have emails after enrichment")
    all_leads.extend(leads)

added = gm.append_leads(all_leads)
gm.log(f"NEW LEADS APPENDED: {added}")
gm.rebuild_excel()
gm.git_commit()
gm.log("=== GMAPS AMMO TOP-UP COMPLETE ===")
