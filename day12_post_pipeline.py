#!/usr/bin/env python3
"""Day-12 post-wave pipeline: wait for the email wave + IG pass to finish, then
  1. run the IG follow+DM pass over every lead that still needs it
  2. rebuild HWA_Lead_Tracker.xlsx (canonical rebuild with Day Summary)
  3. rebuild WA_Pending_List.xlsx
  4. copy both + leads.csv into business-backup, commit and push
  5. print the final verification counts

Runs as one background chain so the steps never overlap with the wave.
"""
import subprocess, sys, time, os

PY = '/home/ubuntu/.hermes/tools/python-3.14.7+20260901-linux-arm64/bin/python3'
LOG = '/home/ubuntu/day12_pipeline_log.txt'


def log(m):
    line = time.strftime('%H:%M:%S') + ' ' + m
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')


def run(cmd, label):
    log(f"--- {label} ---")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    out = (r.stdout or '') + (r.stderr or '')
    log(f"{label} rc={r.returncode}")
    for line in out.strip().splitlines()[-25:]:
        log('   ' + line)
    return r.returncode


log('=== DAY12 POST-WAVE PIPELINE START ===')

# 1. wait for the wave to finish
while True:
    out = subprocess.run(['ps', 'aux'], capture_output=True, text=True).stdout
    if 'day12_wave_runner.py' not in out:
        break
    log('waiting for the email wave...')
    time.sleep(60)
log('email wave finished')

# 2. IG pass
run([PY, '/home/ubuntu/day12_ig_pass.py', '60'], 'IG FOLLOW+DM PASS')

# 3. tracker rebuild (canonical: Leads + Summary + Day Summary + Countries)
run([PY, '/home/ubuntu/rebuild_tracker_day.py'], 'TRACKER REBUILD')

# 4. WA pending list
run([PY, '/home/ubuntu/make_wa_excel.py'], 'WA PENDING LIST')

# 5. git backup
for src in ('/home/ubuntu/leads.csv', '/home/ubuntu/HWA_Lead_Tracker.xlsx',
            '/home/ubuntu/WA_Pending_List.xlsx'):
    dst = os.path.join('/home/ubuntu/business-backup', os.path.basename(src))
    subprocess.run(['cp', '-f', src, dst], check=False)
    log(f'copied {src} -> {dst}')

env = dict(os.environ)
env['GIT_SSH_COMMAND'] = 'ssh -i /home/ubuntu/.ssh/hsn_backup_key -o IdentitiesOnly=yes'
r = subprocess.run(['git', 'add', '-A'], cwd='/home/ubuntu/business-backup',
                   capture_output=True, text=True, env=env)
log(f'git add rc={r.returncode} {r.stdout[:120]}{r.stderr[:120]}')
r = subprocess.run(['git', 'commit', '-m', 'day12 outreach 2026-10-26 (email wave + IG pass + tracker)'],
                   cwd='/home/ubuntu/business-backup', capture_output=True, text=True, env=env)
log(f'git commit rc={r.returncode}: {(r.stdout + r.stderr).strip()[:200]}')
r = subprocess.run(['git', 'push', 'origin', 'main'], cwd='/home/ubuntu/business-backup',
                   capture_output=True, text=True, env=env)
log(f'git push rc={r.returncode}: {(r.stdout + r.stderr).strip()[:200]}')

# 6. final counts
run([PY, '/home/ubuntu/day12_verify.py'], 'FINAL VERIFY')
log('=== DAY12 POST-WAVE PIPELINE COMPLETE ===')
