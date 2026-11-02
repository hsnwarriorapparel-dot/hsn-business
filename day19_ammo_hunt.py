#!/usr/bin/env python3
"""Day-19 (2026-11-02 night) ammo top-up hunt.

True QA-eligible ammo after the Day-19 wave was 63, below the 100 target, so
the hunt runs tonight to bank fresh leads for tomorrow's wave.

FRESH cities never scraped before (verified against leads.csv City values):
  - Charlotte NC (USA - the user's priority market uses email mostly)
  - Portland OR (USA)
  - Columbus OH (USA)

Per-city append: each city is appended to leads.csv as soon as it finishes, so
partial progress is banked even if the session dies. The script is the ONLY
leads.csv writer while it runs - the email wave must not start until this
finishes (full-file CSV writer race).
"""
import sys, os, time, subprocess, importlib.util, glob, json

spec = importlib.util.spec_from_file_location("gmaps_daily_scrape", "/home/ubuntu/gmaps_daily_scrape.py")
gm = importlib.util.module_from_spec(spec)
sys.modules["gmaps_daily_scrape"] = gm
spec.loader.exec_module(gm)

DATE_TAG = "2026-11-02-ammo-hunt"
gm.DATE = DATE_TAG

LOG = '/home/ubuntu/day19_hunt_log.txt'


def hlog(m):
    line = time.strftime('%H:%M:%S') + ' ' + m
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')


# ---- wait for any other writer to finish (never two leads.csv writers) ----
MARKERS = ('day19_wave_runner.py', 'day19_ig_pass.py', 'day19_post_pipeline.py',
           'gmaps_daily_scrape.py', 'day19_ig_hunt.py', 'day19_ig_hunt_backlog.py')
while True:
    out = subprocess.run(['ps', 'aux'], capture_output=True, text=True).stdout
    busy = [m for m in MARKERS if m in out]
    if not busy:
        break
    hlog(f"waiting for {busy} to finish before the hunt...")
    time.sleep(60)

# Never run two gmaps instances at once (throttle risk + duplicate engine jobs).
LOCK = '/home/ubuntu/.hermes/cache/scratch/gmaps_hunt.lock'
if os.path.exists(LOCK):
    hlog('another hunt instance holds the lock - exiting')
    raise SystemExit(0)
with open(LOCK, 'w') as f:
    f.write(str(os.getpid()))

# ---- FRESH cities: never scraped before ----
NEW_CITIES = [
    ("Charlotte NC", "35.2271", "-80.8431", "USA", "+1"),
    ("Portland OR", "45.5152", "-122.6784", "USA", "+1"),
    ("Columbus OH", "39.9612", "-82.9988", "USA", "+1"),
]

hlog(f"=== DAY19 AMMO HUNT START ({DATE_TAG}) cities: {[c[0] for c in NEW_CITIES]} ===")
gm.ensure_engine()

total_added = 0
for city, lat, lon, country, prefix in NEW_CITIES:
    try:
        hlog(f"--- {city} ---")
        leads = gm.run_city(city, lat, lon, country, prefix)
        if not leads:
            hlog(f"{city}: no results")
            continue
        no_email = [l for l in leads if not l["email"] and l["website"]]
        hlog(f"{city}: enriching {len(no_email)} websites for emails")
        for l in no_email:
            gm.enrich_website(l)
        got = sum(1 for l in leads if l["email"])
        hlog(f"{city}: {got}/{len(leads)} have emails after enrichment")
        added = gm.append_leads(leads)
        total_added += added
        hlog(f"{city}: NEW LEADS APPENDED: {added} (running total {total_added})")
    except Exception as e:
        hlog(f"{city}: ERROR {str(e)[:140]}")

hlog(f"=== DAY19 AMMO HUNT COMPLETE: {total_added} new leads appended ===")

# tracker rebuild (canonical - keeps the Day Summary / Summary / Countries sheets)
_c = sorted(glob.glob('/home/ubuntu/.hermes/tools/python-3*/bin/python3'))
PY = _c[0] if _c else sys.executable
r = subprocess.run([PY, '/home/ubuntu/rebuild_tracker_day.py'], capture_output=True, text=True)
hlog('tracker rebuild: ' + ((r.stdout or '').strip().replace('\n', ' | ')[:300] or (r.stderr or '')[:200]))
gm.git_commit()
hlog('git backup done')
try:
    os.unlink(LOCK)
except Exception:
    pass
hlog('=== DAY19 AMMO HUNT END ===')
