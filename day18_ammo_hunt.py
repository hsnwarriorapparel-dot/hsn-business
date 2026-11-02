#!/usr/bin/env python3
"""Day-18 (2026-11-01 night) ammo top-up hunt.

All 24 cities in the gmaps_daily_scrape CITIES pool were already scraped
(the pool now covers Houston..Zurich, Las Vegas + Detroit included), so this
hunt uses THREE FRESH cities that were never scraped before:
  - Nashville TN (USA, email-first market per the user's USA-day rule)
  - San Diego CA (USA)
  - Munich (Germany, EU)

Per-city append: each city is appended to leads.csv as soon as it finishes, so
partial progress is banked even if the session dies. The script is launched via
terminal(background=True) AND is the ONLY leads.csv writer while it runs - the
email wave must not start until this finishes (full-file CSV writer race).
"""
import sys, os, time, subprocess, importlib.util, glob, json

spec = importlib.util.spec_from_file_location("gmaps_daily_scrape", "/home/ubuntu/gmaps_daily_scrape.py")
gm = importlib.util.module_from_spec(spec)
sys.modules["gmaps_daily_scrape"] = gm
spec.loader.exec_module(gm)

DATE_TAG = "2026-11-01-ammo-hunt"
gm.DATE = DATE_TAG

LOG = '/home/ubuntu/day18_hunt_log.txt'


def hlog(m):
    line = time.strftime('%H:%M:%S') + ' ' + m
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')


# ---- wait for any other writer to finish (never two leads.csv writers) ----
MARKERS = ('day18_wave_runner.py', 'day18_ig_pass.py', 'day18_post_pipeline.py',
           'gmaps_daily_scrape.py', 'day17_ig_hunt.py', 'day17_ig_hunt_backlog.py')
while True:
    out = subprocess.run(['ps', 'aux'], capture_output=True, text=True).stdout
    busy = [m for m in MARKERS if m in out]
    if not busy:
        break
    hlog(f"waiting for {busy} to finish before the hunt...")
    time.sleep(60)

# Never run two gmaps instances at once (throttle risk + duplicate engine jobs).
if os.path.exists('/home/ubuntu/.hermes/cache/scratch/gmaps_hunt.lock'):
    hlog('another hunt instance holds the lock - exiting')
    raise SystemExit(0)
with open('/home/ubuntu/.hermes/cache/scratch/gmaps_hunt.lock', 'w') as f:
    f.write(str(os.getpid()))

# ---- FRESH cities: never scraped before (verified against the engine job list) ----
NEW_CITIES = [
    ("Nashville TN", "36.1627", "-86.7816", "USA", "+1"),
    ("San Diego CA", "32.7157", "-117.1611", "USA", "+1"),
    ("Munich", "48.1351", "11.5820", "Germany", "+49"),
]

hlog(f"=== DAY18 AMMO HUNT START ({DATE_TAG}) cities: {[c[0] for c in NEW_CITIES]} ===")
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

hlog(f"=== DAY18 AMMO HUNT COMPLETE: {total_added} new leads appended ===")

# tracker rebuild (canonical - keeps the Day Summary / Summary / Countries sheets)
_c = sorted(glob.glob('/home/ubuntu/.hermes/tools/python-3*/bin/python3'))
PY = _c[0] if _c else sys.executable
r = subprocess.run([PY, '/home/ubuntu/rebuild_tracker_day.py'], capture_output=True, text=True)
hlog('tracker rebuild: ' + ((r.stdout or '').strip().replace('\n', ' | ')[:300] or (r.stderr or '')[:200]))
gm.git_commit()
hlog('git backup done')
try:
    os.unlink('/home/ubuntu/.hermes/cache/scratch/gmaps_hunt.lock')
except Exception:
    pass
hlog('=== DAY18 AMMO HUNT END ===')
