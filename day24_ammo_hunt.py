#!/usr/bin/env python3
"""Day-24 (2026-11-07 night) ammo top-up hunt.

Ammo dropped to 20 after the Day-23 wave (target 100), so the hunt runs to
bank fresh leads for tomorrow's wave.

FRESH markets: the tracker has 116 cities but the EU is badly under-mined -
Greece, Croatia, Hungary, Slovenia, Poland, Austria and Denmark have only
8-29 leads between them, and Norway/Finland/Greece/Croatia/Hungary/Slovenia
have ZERO. These are fresh gmaps markets, so every lead is new supply.

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

DATE_TAG = "2026-11-07-ammo-hunt"
gm.DATE = DATE_TAG

LOG = '/home/ubuntu/day24_hunt_log.txt'


def hlog(m):
    line = time.strftime('%H:%M:%S') + ' ' + m
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')


# ---- wait for any other writer to finish (never two leads.csv writers) ----
MARKERS = ('day24_wave_runner.py', 'day24_ig_pass.py', 'day24_post_pipeline.py',
           'gmaps_daily_scrape.py', 'day24_ig_hunt.py', 'day24_ig_hunt_backlog.py',
           'day23_wave_runner.py', 'day23_ig_pass.py', 'day23_post_pipeline.py',
           'run_today_outreach.py')
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
    try:
        with open(LOCK) as f:
            owner = int(f.read().strip())
        os.kill(owner, 0)
        hlog('another hunt instance (pid %d) holds the lock - exiting' % owner)
        raise SystemExit(0)
    except (ProcessLookupError, ValueError):
        hlog('stale hunt lock found - reclaiming')
        os.unlink(LOCK)
with open(LOCK, 'w') as f:
    f.write(str(os.getpid()))

# ---- FRESH markets: not in the CITIES pool, not yet in leads.csv ----
NEW_CITIES = [
    ("Athens GR", "37.9838", "23.7275", "Greece", "+30"),
    ("Thessaloniki GR", "40.6401", "22.9444", "Greece", "+30"),
    ("Warsaw PL", "52.2297", "21.0122", "Poland", "+48"),
    ("Krakow PL", "50.0647", "19.9450", "Poland", "+48"),
    ("Vienna AT", "48.2082", "16.3738", "Austria", "+43"),
    ("Graz AT", "47.0707", "15.4395", "Austria", "+43"),
    ("Copenhagen DK", "55.6761", "12.5683", "Denmark", "+45"),
    ("Brussels BE", "50.8503", "4.3517", "Belgium", "+32"),
    ("Antwerp BE", "51.2194", "4.4025", "Belgium", "+32"),
    ("Ljubljana SI", "46.0569", "14.5058", "Slovenia", "+386"),
    ("Zagreb HR", "45.8150", "15.9819", "Croatia", "+385"),
    ("Budapest HU", "47.4979", "19.0402", "Hungary", "+36"),
]

hlog(f"=== DAY24 AMMO HUNT START ({DATE_TAG}) cities: {[c[0] for c in NEW_CITIES]} ===")
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

hlog(f"=== DAY24 AMMO HUNT COMPLETE: {total_added} new leads appended ===")

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
hlog('=== DAY24 AMMO HUNT END ===')
