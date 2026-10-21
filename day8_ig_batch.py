#!/usr/bin/env python3
"""Day 8 IG batch: follow + DM every Day-8 hunted lead with a valid IG handle.
Row-targeted status writes via safe_csv_update (never full-file rewrite).
Anti-block: 20-38s random between leads. Skips junk/contaminated handles."""
import sys, time, csv, random
sys.path.insert(0, '/home/ubuntu')
from outreach import ig_open_profile, ig_follow, ig_dm
from templates import build_dm
from cdp_helper import get_tabs, connect
from safe_csv_update import safe_update

CSV = '/home/ubuntu/leads.csv'
LOG = '/home/ubuntu/day8_ig_log.txt'

def log(m):
    line = f"{time.strftime('%H:%M:%S')} {m}"
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + "\n")

def load():
    with open(CSV, newline='', encoding='utf-8') as f:
        return list(csv.reader(f))

JUNK = ['squarespace', 'wix', 'jiujitsudotcom', 'embed', 'instagram', 'facebook',
        'wordpress', 'google', 'youtube', 'mail.', 'tiptoe', 'gymshark', 'p', 'explore',
        'reel', 'direct', 'share', 'static', 'about']

def main():
    rows = load()
    idx = {h: i for i, h in enumerate(rows[0])}
    targets = []
    for r in rows[1:]:
        notes = (r[idx['Notes']] or '')
        st = (r[idx['Status']] or '').lower()
        h = (r[idx['IG Username']] or '').strip().lstrip('@')
        if 'Day 8' not in notes and 'day 8' not in st:
            continue
        if not h or h.lower() in JUNK:
            continue
        if any(m in st for m in ['follow', 'dm=', 'notfound', 'not found', 'ig=']):
            continue
        if 'wrestling' in h.lower() or 'badminton' in h.lower() or 'club' in h.lower() and 'wrestl' in h.lower():
            pass  # not filtering by name here; the pipeline already marked NOTFOUND ones
        targets.append((r[0], r[idx['Name']], h, r[idx['Country']] or 'Europe'))
    log(f"DAY 8 IG BATCH START: {len(targets)} profiles to follow+DM")
    done = fails = 0
    for lid, name, h, country in targets:
        try:
            ok = ig_open_profile(h)
            if not ok:
                safe_update(lid, append_status='IG profile not found (Day 8 batch)')
                fails += 1
                log(f"  NOTFOUND {name[:24]} @{h}")
                time.sleep(8)
                continue
            tab = [t for t in get_tabs() if f'instagram.com/{h}' in t['url'] and t['type'] == 'page']
            if not tab:
                log(f"  ERR {lid}: no tab for @{h}")
                fails += 1
                continue
            ws = connect(tab[-1])
            fr = ig_follow(ws)
            time.sleep(3)
            dm = ig_dm(ws, build_dm(name, f"martial arts gym in {country}"))
            ws.close()
            safe_update(lid, append_status=f"IG follow={fr} dm={dm} (Day 8)")
            done += 1
            log(f"  OK {name[:24]} @{h} follow={fr} dm={dm}")
            time.sleep(random.randint(20, 38))
        except Exception as e:
            fails += 1
            log(f"  ERROR {lid} @{h}: {str(e)[:50]}")
            time.sleep(10)
    log(f"DAY 8 IG BATCH DONE: {done} followed+DM'd, {fails} failed/notfound")

if __name__ == '__main__':
    main()
