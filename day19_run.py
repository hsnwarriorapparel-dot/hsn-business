#!/usr/bin/env python3
"""Day-19 (2026-11-02) master orchestrator.

Chain (never overlapping, so leads.csv always has exactly ONE writer):
  1. wait for the ammo hunt to finish (it appends leads.csv)
  2. site-verify the ammo pool (read-only on leads.csv)
  3. build the 100-lead wave with the proven QA rules
  4. fire the email wave (row-targeted status writes, exclusive lock)
  5. post pipeline: IG handle hunt -> IG follow+DM -> tracker rebuild ->
     WA pending list -> git backup -> reply sweep -> final verify

The email wave is resumable and the system-crontab wave_guard.sh can restart
it if this process dies, so a truncated wave is recovered rather than lost.
"""
import subprocess, sys, os, glob, time

_c = sorted(glob.glob('/home/ubuntu/.hermes/tools/python-3*/bin/python3'))
PY = _c[0] if _c else sys.executable
LOG = '/home/ubuntu/day19_run_log.txt'


def log(m):
    line = time.strftime('%H:%M:%S') + ' ' + m
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')


def run(cmd, label, timeout=14400):
    log(f'--- {label} ---')
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        log(f'{label} TIMEOUT after {int(time.time()-t0)}s')
        return 124
    out = ((r.stdout or '') + (r.stderr or '')).strip()
    log(f'{label} rc={r.returncode} ({int(time.time()-t0)}s)')
    for line in out.splitlines()[-45:]:
        log('   ' + line[:200])
    return r.returncode


def proc_running(pattern):
    out = subprocess.run(['ps', 'aux'], capture_output=True, text=True).stdout
    return pattern in out


log('=== DAY19 MASTER RUN START ===')

# 1. wait for the ammo hunt
while proc_running('day19_ammo_hunt.py'):
    log('waiting for the ammo hunt to finish...')
    time.sleep(45)
log('ammo hunt finished')

# safety: no other leads.csv writer may be alive
while proc_running('gmaps_daily_scrape.py'):
    log('waiting for gmaps_daily_scrape to finish...')
    time.sleep(30)

# 2. site verification (read-only)
run([PY, '/home/ubuntu/day19_site_verify.py'], 'SITE VERIFY')

# 3. build the wave
run([PY, '/home/ubuntu/day19_build_wave.py'], 'BUILD WAVE')

# 4. fire the wave (resumable - re-run until every wave lead is terminal)
def wave_unsent():
    """Count wave leads that are not yet sent/failed/excluded (guard logic)."""
    import csv as _csv
    ids = [l.strip() for l in open('/home/ubuntu/day19_wave.txt') if l.strip()]
    rows = {}
    with open('/home/ubuntu/leads.csv', encoding='utf-8-sig', errors='replace') as f:
        for r in _csv.DictReader(f):
            rows[(r.get('Lead ID') or '').strip()] = (r.get('Status') or '').lower()
    n = 0
    for lid in ids:
        st = rows.get(lid, '')
        if 'email sent' in st or 'failed' in st or 'excluded' in st or 're-hunt' in st:
            continue
        n += 1
    return n


for attempt in range(1, 5):
    # Never race the system-crontab wave_guard: wait until no runner holds
    # the wave lock before launching our own pass.
    for _ in range(60):
        if not proc_running('day19_wave_runner.py') and not os.path.exists('/home/ubuntu/day19_wave.lock'):
            break
        time.sleep(10)
    rc = run([PY, '/home/ubuntu/day19_wave_runner.py'], f'EMAIL WAVE (pass {attempt})')
    pending = wave_unsent()
    log(f'wave pass {attempt}: rc={rc} pending={pending}')
    if pending == 0:
        log('wave fully resolved (every wave lead is sent/failed/excluded)')
        break
    log(f'{pending} wave lead(s) still pending - resuming the wave')
    time.sleep(20)
else:
    log('WARNING: wave still has pending leads after 4 passes')

# 5. post pipeline (IG hunt -> IG pass -> tracker -> backup -> sweep -> verify)
run([PY, '/home/ubuntu/day19_post_pipeline.py'], 'POST PIPELINE')

log('=== DAY19 MASTER RUN COMPLETE ===')
