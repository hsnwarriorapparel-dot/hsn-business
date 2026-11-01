#!/usr/bin/env python3
"""Day-17 ammo top-up (2026-10-31 night): scrape 2 cities that have NEVER been
scraped (Las Vegas NV and Detroit MI have 0 leads in leads.csv), then append
deduped leads with verified emails.

Runs AFTER the email wave + IG pass finish, so the two CSV writers never
touch leads.csv at the same time.
Cities are chosen from the 24-city pool by NAME (never by a guessed index).
"""
import sys, os, time, subprocess, importlib.util

spec = importlib.util.spec_from_file_location("gmaps_daily_scrape", "/home/ubuntu/gmaps_daily_scrape.py")
gm = importlib.util.module_from_spec(spec)
sys.modules["gmaps_daily_scrape"] = gm
spec.loader.exec_module(gm)

DATE_TAG = "2026-10-31-ammo-topup"

# ---- wait for the email wave + IG pass to finish (never write leads.csv concurrently) ----
MARKERS = ('day17_wave_runner.py', 'day17_ig_pass.py', 'day17_post_pipeline.py')
while True:
    out = subprocess.run(['ps', 'aux'], capture_output=True, text=True).stdout
    busy = [m for m in MARKERS if m in out]
    if not busy:
        break
    gm.log(f"waiting for {busy} to finish before the top-up...")
    time.sleep(60)

gm.DATE = DATE_TAG

# Las Vegas NV and Detroit MI have ZERO leads in the tracker - never scraped.
PICKS = [c for c in gm.CITIES if c[0] in ("Las Vegas NV", "Detroit MI")]
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
PY = sorted(__import__('glob').glob('/home/ubuntu/.hermes/tools/python-3*/bin/python3'))[0]
r = subprocess.run([PY, '/home/ubuntu/rebuild_tracker_day.py'], capture_output=True, text=True)
gm.log('tracker rebuild: ' + (r.stdout.strip().replace('\n', ' | ')[:300] or r.stderr[:200]))
gm.git_commit()
gm.log("=== GMAPS AMMO TOP-UP COMPLETE ===")
