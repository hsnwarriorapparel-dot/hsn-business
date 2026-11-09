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
import subprocess, sys, time, os, glob, json, datetime

# discover the absolute interpreter path (never hardcode a numeric-looking dir:
# it gets redacted in tool output and would silently corrupt the path)
_cands = sorted(glob.glob('/home/ubuntu/.hermes/tools/python-3*/bin/python3'))
PY = _cands[0] if _cands else sys.executable
LOG = '/home/ubuntu/day24_pipeline_log.txt'


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


log('=== DAY24 POST-WAVE PIPELINE START ===')

# 1. wait for the wave to finish
while True:
    out = subprocess.run(['ps', 'aux'], capture_output=True, text=True).stdout
    if 'day24_wave_runner.py' not in out:
        break
    log('waiting for the email wave...')
    time.sleep(60)
log('email wave finished')

# 2. Take the wave lock NOW (the runner released it when it exited). Holding
#    it stops the system-crontab wave_guard from spawning a competing runner
#    while this pipeline runs - two runners race on one Gmail tab and race on
#    leads.csv (observed 2026-11-05: 9 leads double-processed).
LOCK = '/home/ubuntu/day24_wave.lock'
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
run([PY, '/home/ubuntu/day24_ig_hunt.py'], 'IG HANDLE HUNT (today wave)')
run([PY, '/home/ubuntu/day24_ig_hunt_backlog.py'], 'IG HANDLE HUNT (backlog + today)')

# 3. IG follow+DM pass: today's wave leads + today's other hunted leads first
# IG PASS SIZE - MEASURED, NOT GUESSED.
#
# The pass was set to 240 accounts. The measured cost is 37.4 seconds per
# account, so 240 accounts needs 2.5 HOURS - and the cron gives this
# pipeline 3600 seconds. The pass was killed every single night at the
# 1-hour mark, which meant the pipeline NEVER reached the tracker
# rebuild, the WA list, the reply sweep or the final verify.
# The job failed three nights running and nobody noticed, because the
# log's last line was a normal-looking progress line.
#
# 70 accounts x 37.4s = 44 minutes, which fits inside the window with
# room for the hunt steps that run before it. The pass is RESUMABLE - it
# skips any handle already touched - so the remainder is picked up on
# the next night.
IG_PASS_BATCH = 70
run([PY, '/home/ubuntu/day24_ig_pass.py', str(IG_PASS_BATCH)], 'IG FOLLOW+DM PASS')

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
for pat in ('day24_*.py', 'day24_wave.txt', 'day24_wave_detail.csv'):
    for src in glob.glob('/home/ubuntu/' + pat):
        subprocess.run(['cp', '-f', src,
                        os.path.join('/home/ubuntu/business-backup', os.path.basename(src))],
                       check=False)
log('copied day24 scripts into business-backup')

env = dict(os.environ)
env['GIT_SSH_COMMAND'] = 'ssh -i /home/ubuntu/.ssh/hsn_backup_key -o IdentitiesOnly=yes'
r = subprocess.run(['git', 'add', '-A'], cwd='/home/ubuntu/business-backup',
                   capture_output=True, text=True, env=env)
log(f'git add rc={r.returncode} {r.stdout[:120]}{r.stderr[:120]}')
r = subprocess.run(['git', 'commit', '-m', 'day24 outreach 2026-11-05 (email wave + IG pass + tracker)'],
                   cwd='/home/ubuntu/business-backup', capture_output=True, text=True, env=env)
log(f'git commit rc={r.returncode}: {(r.stdout + r.stderr).strip()[:200]}')
r = subprocess.run(['git', 'push', 'origin', 'main'], cwd='/home/ubuntu/business-backup',
                   capture_output=True, text=True, env=env)
log(f'git push rc={r.returncode}: {(r.stdout + r.stderr).strip()[:200]}')

# 6. final counts
run([PY, '/home/ubuntu/day24_reply_sweep.py'], 'REPLY SWEEP + STOP MARKING')
run([PY, '/home/ubuntu/day24_verify.py'], 'FINAL VERIFY')

# COMPLETION MARKER.
#
# The pipeline was killed by the 1-hour cron timeout inside the IG pass,
# three nights running. The log's last line was an ordinary progress
# line, so the failure looked like a normal run that happened to stop.
# The tracker rebuild, the WA list, the reply sweep and the final verify
# were never reached and nothing said so.
#
# Write a marker ONLY when every step above has run. The watchdog then
# checks for it, and a missing marker is reported instead of passing
# silently.
try:
    with open('/home/ubuntu/pipeline_completed.json', 'w') as _f:
        json.dump({'date': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d'),
                   'at': datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S'),
                   'ig_batch': IG_PASS_BATCH}, _f, indent=2)
    log('PIPELINE COMPLETED - all steps ran')
except Exception as _e:
    log('could not write the completion marker: %s' % _e)

# release the lock so tomorrow's guard is free
try:
    if os.path.exists(LOCK):
        os.unlink(LOCK)
        log('wave lock released')
except Exception as e:
    log('lock release warning:', str(e)[:60])

log('=== DAY24 POST-WAVE PIPELINE COMPLETE ===')
