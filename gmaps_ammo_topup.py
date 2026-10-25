#!/usr/bin/env python3
"""Ad-hoc gmaps hunt for top-up ammo (Day 11, 2026-10-25).
Runs the proven gmaps_daily_scrape functions for TWO cities outside today's
rotation (today = Milan + Rome), then appends deduped leads, rebuilds the
tracker and commits+pushes. Read-only against leads.csv except the append
(written by append_leads, which is row-targeted and dedupes).
"""
import sys, datetime, importlib.util

spec = importlib.util.spec_from_file_location("gmaps_daily_scrape", "/home/ubuntu/gmaps_daily_scrape.py")
gm = importlib.util.module_from_spec(spec)
sys.modules["gmaps_daily_scrape"] = gm
spec.loader.exec_module(gm)

gm.DATE = "2026-10-25-ammo-topup"
# Cities OUTSIDE today's rotation (today used Milan + Rome), not scraped
# recently: Lisbon + Zurich.
PICKS = [gm.CITIES[22], gm.CITIES[23]]  # Lisbon, Zurich

gm.log("=== GMAPS AMMO TOP-UP START ===")
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
