#!/usr/bin/env python3
"""Day 4 night sender: emails all pending Day-4 leads + IG follow/DM fallback for failed ones.
NO WhatsApp sends (banned). Waits until leads exist, processes them in batches with anti-block delays.
"""
import subprocess, re, csv, time, sys, os
sys.path.insert(0, '/home/ubuntu')

CSV = '/home/ubuntu/leads.csv'
LOG = '/home/ubuntu/day4_log.txt'
PY = '/home/ubuntu/.hermes/tools/python-3.14.7+20260901-linux-arm64/bin/python3'

def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + "\n")

def send_email_via_hermes(name, email, detail):
    """Calls the working gmail_send from outreach.py using the Hermes python."""
    code = f'''
import sys; sys.path.insert(0, '/home/ubuntu')
from outreach import gmail_send
from templates import build_email
subject, body = build_email({name!r}, {detail!r})
r = gmail_send({email!r}, subject, body)
print("RESULT:" + str(r))
'''
    r = subprocess.run([PY, '-c', code], capture_output=True, text=True, timeout=120)
    out = r.stdout
    for line in out.splitlines():
        if line.startswith('RESULT:'):
            return line[7:].strip()
    return 'error-no-result'

def load_pending():
    with open(CSV) as f:
        rows = list(csv.reader(f))
    idx = {h: i for i, h in enumerate(rows[0])}
    pend = []
    for r in rows[1:]:
        if 'Day 4' in r[idx['Notes']] and 'outreach pending' in r[idx['Status']]:
            pend.append({'row': r, 'idx': idx})
    return pend, idx

def update_status(lead_id, new_status):
    with open(CSV) as f:
        rows = list(csv.reader(f))
    idx = {h: i for i, h in enumerate(rows[0])}
    for r in rows[1:]:
        if r[0] == lead_id:
            r[idx['Status']] = new_status
    with open(CSV, 'w', newline='') as f:
        csv.writer(f).writerows(rows)

def main():
    log("SENDER WAITING for leads from hunter...")
    # poll until hunter has produced leads, then send in waves every 30 min
    idle_rounds = 0
    while idle_rounds < 3:  # give up after 3 empty checks post-hunt
        pending, idx = load_pending()
        if not pending:
            # check if hunter is still running
            hunter_alive = subprocess.run(['pgrep', '-f', 'day4_email_hunter'], capture_output=True).returncode == 0
            if hunter_alive:
                log("No pending leads yet (hunter still running). Waiting 10 min...")
                time.sleep(600)
                continue
            idle_rounds += 1
            log(f"No pending, hunter done. Idle round {idle_rounds}/3. Waiting 15 min...")
            time.sleep(900)
            continue
        idle_rounds = 0
        log(f"Processing {len(pending)} pending leads")
        sent = 0
        for p in pending:
            r = p['row']; i = p['idx']
            lid, name, email = r[0], r[1], r[i['Email']]
            if not email:
                update_status(lid, 'NO EMAIL - IG fallback needed')
                continue
            detail = f"martial arts gym in {r[i['Country']] or 'Europe'}"
            res = send_email_via_hermes(name, email, detail)
            if res == 'sent':
                update_status(lid, f'COMPLETE: email sent')
                sent += 1
                log(f"  EMAIL OK {name} <{email}>")
            else:
                update_status(lid, f'EMAIL FAILED: {res[:60]} - IG fallback needed')
                log(f"  EMAIL FAIL {name} <{email}>: {res[:50]}")
            time.sleep(random_wait())
        log(f"Wave done: {sent} emails sent. Cooling 20 min before next wave...")
        time.sleep(1200)
    log("SENDER FINISHED")

def random_wait():
    import random
    return random.randint(25, 45)  # 25-45s between emails: ~50-70/hour — safe for Gmail



# === IG EMAIL HUNT PASS (added per user instruction 2026-10-14) ===
# Leads marked "NO EMAIL - IG fallback needed" get: hunt email via their IG profile, 
# then email them if found; regardless: IG follow + DM.
def ig_fallback_pass():
    """For all Day-4 leads without sent emails: follow + DM (+ try to hunt email from IG)."""
    from ig_email_extractor import extract_from_profile
    from outreach import ig_open_profile, ig_follow, ig_dm
    from templates import build_dm
    from cdp_helper import get_tabs, connect
    with open(CSV) as f:
        rows = list(csv.reader(f))
    idx = {h: i for i, h in enumerate(rows[0])}
    targets = []
    for r in rows[1:]:
        if 'Day 4' in r[idx['Notes']] and ('IG fallback' in r[idx['Status']] or 'NO EMAIL' in r[idx['Status']] or 'EMAIL FAILED' in r[idx['Status']]):
            targets.append(r)
    log(f"IG FALLBACK: {len(targets)} leads to follow+DM")
    for r in targets:
        lid, name, country = r[0], r[1], r[idx['Country']]
        handle = (r[idx['IG Username']] or '').lstrip('@')
        status_new = []
        # try email extraction from IG if handle exists
        hunted_email = None
        if handle:
            try:
                d = extract_from_profile(handle)
                if d and d.get('email'):
                    hunted_email = d['email']
                    log(f"  IG-hunted email for {name}: {hunted_email}")
            except Exception as e:
                log(f"  IG extract fail {name}: {e}")
        if hunted_email:
            res = send_email_via_hermes(name, hunted_email, f"martial arts gym in {country or 'Europe'}")
            if res == 'sent':
                status_new.append('email sent (hunted from IG)')
                # update email field
                with open(CSV) as f2:
                    rows2 = list(csv.reader(f2))
                idx2 = {h: i for i, h in enumerate(rows2[0])}
                for rr in rows2[1:]:
                    if rr[0] == lid:
                        rr[idx2['Email']] = hunted_email
                with open(CSV, 'w', newline='') as f2:
                    csv.writer(f2).writerows(rows2)
            else:
                status_new.append(f'email hunt failed: {res[:40]}')
        # follow + DM regardless
        if handle:
            try:
                ok = ig_open_profile(handle)
                if ok:
                    tab = [t for t in get_tabs() if f'instagram.com/{handle}' in t['url'] and t['type']=='page']
                    ws = connect(tab[-1])
                    fr = ig_follow(ws)
                    time.sleep(3)
                    dm = ig_dm(ws, build_dm(name, f"martial arts gym in {country or 'Europe'}"))
                    ws.close()
                    status_new.append(f'IG follow={fr} dm={dm}')
                    log(f"  IG {name}: follow={fr} dm={dm}")
                    time.sleep(20)
            except Exception as e:
                status_new.append(f'IG error: {str(e)[:40]}')
        update_status(lid, 'COMPLETE: ' + ' | '.join(status_new) if status_new else 'COMPLETE: no channels')
    log("IG FALLBACK PASS DONE")

# run fallback at the end of main()
_orig_main = main
def main_with_fallback():
    _orig_main()
    log("Starting IG fallback pass...")
    ig_fallback_pass()


if __name__ == '__main__':
    main()
    log('MAIN DONE - running IG fallback pass for emailless leads...')
    try:
        ig_fallback_pass()
    except Exception as e:
        log(f'IG fallback error: {e}')
    log('DAY 4 SENDER FULLY COMPLETE')
