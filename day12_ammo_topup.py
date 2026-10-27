#!/usr/bin/env python3
"""Day-12 ammo top-up: scrape 2 cities that were NOT scraped in the last 2 days,
then append deduped leads with verified emails.

Runs AFTER the email wave finishes (it waits for the wave process to exit, so
the two writers never touch leads.csv at the same time).
Cities are chosen from the 24-city pool by NAME (never by a guessed index).
"""
import sys, os, time, datetime, importlib.util, subprocess

spec = importlib.util.spec_from_file_location("gmaps_daily_scrape", "/home/ubuntu/gmaps_daily_scrape.py")
gm = importlib.util.module_from_spec(spec)
sys.modules["gmaps_daily_scrape"] = gm
spec.loader.exec_module(gm)

DATE_TAG = "2026-10-26-ammo-topup"

# ---- wait for the email wave + IG pass to finish (never write leads.csv concurrently) ----
MARKERS = ('day12_wave_runner.py', 'day12_ig_pass.py')
while True:
    out = subprocess.run(['ps', 'aux'], capture_output=True, text=True).stdout
    busy = [m for m in MARKERS if m in out]
    if not busy:
        break
    gm.log(f"waiting for {busy} to finish before the top-up...")
    time.sleep(60)

gm.DATE = DATE_TAG

# Cities not scraped recently (Dublin = 2026-10-23, Manchester = 2026-10-21)
PICKS = [c for c in gm.CITIES if c[0] in ("Dublin", "Manchester")]
assert len(PICKS) == 2, PICKS

gm.log(f"=== GMAPS AMMO TOP-UP START ({DATE_TAG}) cities: {[p[0] for p in PICKS]} ===")
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
# NOTE: gm.rebuild_excel() writes a flat 2-sheet workbook and would DESTROY the
# Day Summary / Summary / Countries sheets - use the canonical rebuild instead.
r = subprocess.run(['/home/ubuntu/.hermes/tools/python-3.14.7+20260901-linux-arm64/bin/python3',
                    '/home/ubuntu/rebuild_tracker_day.py'], capture_output=True, text=True)
gm.log('tracker rebuild: ' + (r.stdout.strip().replace('\n', ' | ')[:300] or r.stderr[:200]))
gm.git_commit()
gm.log("=== GMAPS AMMO TOP-UP COMPLETE ===")
