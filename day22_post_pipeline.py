#!/usr/bin/env python3
"""Day-22 (2026-11-05) post-wave pipeline.

Runs as one background chain so the steps never overlap with the email wave:
  1. wait for the email wave to finish
  2. IG follow+DM pass over every lead that still needs it
  3. rebuild HWA_Lead_Tracker.xlsx (canonical rebuild with Day Summary)
  4. rebuild WA_Pending_List.xlsx
  5. copy both + leads.csv into business-backup, commit and push
  6. print the final verification counts
"""
import subprocess, sys, time, os, glob

# discover the absolute interpreter path (never hardcode a numeric-looking dir:
# it gets redacted in tool output and would silently corrupt the path)
_cands = sorted(glob.glob('/home/ubuntu/.hermes/tools/python-3*/bin/python3'))
PY = _cands[0] if _cands else sys.executable
LOG = '/home/ubuntu/day22_pipeline_log.txt'


def log(m):
    line = time.strftime('%H:%M:%S') + ' ' + m
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')


# Per-step timeout: the IG follow+DM pass alone measured 2h21m (2026-11-05).
def run(cmd, label, timeout=21600):  # 6h
    log(f"--- {label} ---")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        log(f"{label} TIMEOUT")
        return 124
    out = (r.stdout or '') + (r.stderr or '')
    log(f"{label} rc={r.returncode}")
    for line in out.strip().splitlines()[-30:]:
        log('   ' + line)
    return r.returncode


log('=== DAY22 POST-WAVE PIPELINE START ===')

# 1. wait for the wave to finish
while True:
    out = subprocess.run(['ps', 'aux'], capture_output=True, text=True).stdout
    if 'day22_wave_runner.py' not in out:
        break
    log('waiting for the email wave...')
    time.sleep(60)
log('email wave finished')

# 2. Take the wave lock NOW (the runner released it when it exited). Holding
#    it stops the system-crontab wave_guard from spawning a competing runner
#    while this pipeline runs - two runners race on one Gmail tab and race on
#    leads.csv (observed 2026-11-05: 9 leads double-processed).
LOCK = '/home/ubuntu/day22_wave.lock'
try:
    fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    log('wave lock acquired (pid %s)' % os.getpid())
except FileExistsError:
    log('wave lock already held (stale or another pipeline); continuing')

# 2. IG handle hunt for every lead still missing a handle.
#    This is a FULL-FILE writer, so it MUST run only after the wave is done.
#    Run the WAVE hunt FIRST (it ignores the 'email sent' status and only
#    targets today's wave), then the backlog hunt (which skips leads whose
#    status already contains 'email sent', so it cannot find wave handles).
run([PY, '/home/ubuntu/day22_ig_hunt.py'], 'IG HANDLE HUNT (today wave)')
run([PY, '/home/ubuntu/day22_ig_hunt_backlog.py'], 'IG HANDLE HUNT (backlog + today)')

# 3. IG follow+DM pass: today's wave leads + today's other hunted leads first
run([PY, '/home/ubuntu/day22_ig_pass.py', '240'], 'IG FOLLOW+DM PASS')

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

# keep the run scripts in the backup repo too (day17 pattern)
for pat in ('day22_*.py', 'day22_wave.txt', 'day22_wave_detail.csv'):
    for src in glob.glob('/home/ubuntu/' + pat):
        subprocess.run(['cp', '-f', src,
                        os.path.join('/home/ubuntu/business-backup', os.path.basename(src))],
                       check=False)
log('copied day22 scripts into business-backup')

env = dict(os.environ)
env['GIT_SSH_COMMAND'] = 'ssh -i /home/ubuntu/.ssh/hsn_backup_key -o IdentitiesOnly=yes'
r = subprocess.run(['git', 'add', '-A'], cwd='/home/ubuntu/business-backup',
                   capture_output=True, text=True, env=env)
log(f'git add rc={r.returncode} {r.stdout[:120]}{r.stderr[:120]}')
r = subprocess.run(['git', 'commit', '-m', 'day22 outreach 2026-11-05 (email wave + IG pass + tracker)'],
                   cwd='/home/ubuntu/business-backup', capture_output=True, text=True, env=env)
log(f'git commit rc={r.returncode}: {(r.stdout + r.stderr).strip()[:200]}')
r = subprocess.run(['git', 'push', 'origin', 'main'], cwd='/home/ubuntu/business-backup',
                   capture_output=True, text=True, env=env)
log(f'git push rc={r.returncode}: {(r.stdout + r.stderr).strip()[:200]}')

# 6. final counts
run([PY, '/home/ubuntu/day22_reply_sweep.py'], 'REPLY SWEEP + STOP MARKING')
run([PY, '/home/ubuntu/day22_verify.py'], 'FINAL VERIFY')

# release the lock so tomorrow's guard is free
try:
    if os.path.exists(LOCK):
        os.unlink(LOCK)
        log('wave lock released')
except Exception as e:
    log('lock release warning:', str(e)[:60])

log('=== DAY22 POST-WAVE PIPELINE COMPLETE ===')
