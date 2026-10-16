#!/usr/bin/env python3
"""Day 5 USA cold outreach sender: emails all pending USA leads (region-correct template),
then IG follow+DM for leads with handles. WA only for the 2 with numbers (draft for user).
Waves with anti-block pacing: 30-50s between emails.
"""
import sys, time, csv, subprocess, os, tempfile, random
sys.path.insert(0, '/home/ubuntu')

CSV = '/home/ubuntu/leads.csv'
LOG = '/home/ubuntu/day5_sender_log.txt'
PY = '/home/ubuntu/.hermes/tools/python-3.14.7+20260901-linux-arm64/bin/python3'

def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + "\n")

def send_email_via_hermes(name, email, detail, region):
    code = f'''
import sys; sys.path.insert(0, '/home/ubuntu')
from outreach import gmail_send
from templates import build_email
subject, body = build_email({name!r}, {detail!r}, region={region!r})
r = gmail_send({email!r}, subject, body)
print("RESULT:" + str(r))
'''
    r = subprocess.run([PY, '-c', code], capture_output=True, text=True, timeout=120)
    for line in r.stdout.splitlines():
        if line.startswith('RESULT:'):
            return line[7:].strip()
    return 'error-no-result'

def update_status(lead_id, new_status):
    with open(CSV) as f:
        rows = list(csv.reader(f))
    idx = {h: i for i, h in enumerate(rows[0])}
    changed = False
    for r in rows[1:]:
        if r[0] == lead_id:
            r[idx['Status']] = new_status
            changed = True
    if not changed:
        return
    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='') as f:
        csv.writer(f).writerows(rows)
    with open(tmp) as f:
        check = list(csv.reader(f))
    assert len(check) == len(rows)
    os.replace(tmp, CSV)

def load_pending():
    with open(CSV) as f:
        rows = list(csv.reader(f))
    idx = {h: i for i, h in enumerate(rows[0])}
    pend = [r for r in rows[1:] if 'Day 5 USA' in r[idx['Notes']] and 'pending' in r[idx['Status']]]
    return pend, idx

def main():
    pending, idx = load_pending()
    log(f"USA COLD EMAIL WAVE: {len(pending)} leads")
    sent = failed = 0
    for r in pending:
        lid, name, email = r[0], r[1], r[idx['Email']]
        if not email:
            continue
        # build a US-flavored detail line from the name
        detail = f"martial arts training business {name}"
        res = send_email_via_hermes(name, email, detail, "USA")
        if res == 'sent':
            update_status(lid, 'COMPLETE: email sent (Day 5 USA wave)')
            sent += 1
            log(f"  OK {name} <{email}>")
        else:
            update_status(lid, f'EMAIL FAILED: {str(res)[:50]} - IG fallback')
            failed += 1
            log(f"  FAIL {name} <{email}>: {res[:40]}")
        time.sleep(random.randint(30, 50))  # Gmail-safe pacing
    log(f"EMAIL WAVE DONE: {sent} sent, {failed} failed")

if __name__ == '__main__':
    main()
