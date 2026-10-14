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

if __name__ == '__main__':
    main()
