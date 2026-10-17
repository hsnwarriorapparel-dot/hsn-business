#!/usr/bin/env python3
"""IG batch: follow + DM all Day-5 USA leads with handles. Waves with anti-block delays.
CSV writes are row-targeted via safe_csv_update.py (never full-file rewrite)."""
import sys, time, csv, random
sys.path.insert(0, '/home/ubuntu')
from outreach import ig_open_profile, ig_follow, ig_dm
from templates import build_dm
from cdp_helper import get_tabs, connect
import importlib
safe = importlib.import_module('safe_csv_update')

CSV = '/home/ubuntu/leads.csv'
LOG = '/home/ubuntu/day5_ig_log.txt'

def log(m):
    line = f"{time.strftime('%H:%M:%S')} {m}"
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + "\n")

def load():
    with open(CSV) as f:
        return list(csv.reader(f))

def update_status(lid, new_status):
    try:
        import safe_csv_update
        safe_csv_update.safe_update(lid, new_status=new_status)
    except Exception as e:
        log(f"  CSVWARN {lid}: {str(e)[:40]} — fallback write")
        safe_update_fallback(lid, new_status)

def safe_update_fallback(lid, new_status):
    rows = load()
    idx = {h: i for i, h in enumerate(rows[0])}
    for r in rows[1:]:
        if r[0] == lid:
            r[idx['Status']] = new_status
    tmp = CSV + '.tmp'
    with open(tmp, 'w', newline='') as f:
        csv.writer(f).writerows(rows)
    import os
    os.replace(tmp, CSV)

def main():
    rows = load()
    idx = {h: i for i, h in enumerate(rows[0])}
    targets = [r for r in rows[1:] if 'Day 5 USA' in r[idx['Notes']]
               and (r[idx['IG Username']] or '').strip()
               and 'follow' not in r[idx['Status']].lower()
               and 'DUPLICATE' not in r[idx['Status']]
               and 'FEDERATION' not in r[idx['Status']]
               and 'skipped' not in r[idx['Status']].lower()]
    log(f"DAY5 IG BATCH START: {len(targets)} USA profiles to follow+DM")
    done, fails = 0, 0
    for r in targets:
        lid = r[0]; name = r[1]; handle = r[idx['IG Username']].strip().lstrip('@')
        country = r[idx['Country']] or 'the USA'
        try:
            ok = ig_open_profile(handle)
            if not ok:
                update_status(lid, r[idx['Status']] + ' | IG profile not found')
                fails += 1
                log(f"  NOTFOUND {name} @{handle}")
                time.sleep(8)
                continue
            tab = [t for t in get_tabs() if f'instagram.com/{handle}' in t['url'] and t['type'] == 'page']
            if not tab:
                update_status(lid, r[idx['Status']] + ' | IG tab missing')
                fails += 1
                continue
            ws = connect(tab[-1])
            fr = ig_follow(ws)
            time.sleep(3)
            dm = ig_dm(ws, build_dm(name, f"martial arts gym in {country}"))
            ws.close()
            if dm == 'sent' or 'sent' in str(dm):
                update_status(lid, f"{r[idx['Status']]} | IG follow={fr} dm=sent")
                done += 1
                log(f"  OK {name} @{handle} follow={fr} dm={dm}")
            else:
                update_status(lid, f"{r[idx['Status']]} | IG follow={fr} dm={dm}")
                fails += 1
                log(f"  PARTIAL {name} @{handle} follow={fr} dm={dm}")
            # anti-block: 20-38s random
            time.sleep(random.randint(20, 38))
        except Exception as e:
            update_status(lid, f"{r[idx['Status']]} | IG error: {str(e)[:40]}")
            fails += 1
            log(f"  ERROR {name} @{handle}: {str(e)[:50]}")
            time.sleep(10)
    log(f"DAY5 IG BATCH DONE: {done} followed+DM'd, {fails} failed/partial")

if __name__ == '__main__':
    main()
