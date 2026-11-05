#!/usr/bin/env python3
"""Day-21 (2026-11-04) master orchestrator.

Chain (never overlapping, so leads.csv always has exactly ONE writer):
  1. wait for any running leads.csv writer (gmaps scrape / ammo hunt) to finish
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
LOG = '/home/ubuntu/day21_run_log.txt'


def log(m):
    line = time.strftime('%H:%M:%S') + ' ' + m
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')


# Per-step timeout. The IG follow+DM pass over 240 candidates measured 2h21m
# (2026-11-05) and the reply sweep adds more, so 4h per step was too tight.
def run(cmd, label, timeout=21600):  # 6h
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


log('=== DAY21 MASTER RUN START ===')

# 1. wait for any leads.csv writer to finish (never two writers at once)
for pat in ('gmaps_daily_scrape.py', 'day21_ammo_hunt.py', 'day20_ammo_hunt.py'):
    waited = 0
    while proc_running(pat):
        log(f'waiting for {pat} to finish...')
        time.sleep(45)
        waited += 45
        if waited > 7200:
            log(f'WARNING: {pat} still running after 2h - continuing anyway')
            break

# 2. site verification (read-only)
run([PY, '/home/ubuntu/day21_site_verify.py'], 'SITE VERIFY')

# 3. build the wave
run([PY, '/home/ubuntu/day21_build_wave.py'], 'BUILD WAVE')


def wave_unsent():
    """Count wave leads that are not yet sent/failed/excluded (guard logic)."""
    import csv as _csv
    wf = '/home/ubuntu/day21_wave.txt'
    if not os.path.exists(wf):
        return 0
    ids = [l.strip() for l in open(wf) if l.strip()]
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
        if (not proc_running('day21_wave_runner.py')
                and not os.path.exists('/home/ubuntu/day21_wave.lock')):
            break
        time.sleep(10)
    rc = run([PY, '/home/ubuntu/day21_wave_runner.py'], f'EMAIL WAVE (pass {attempt})')
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
run([PY, '/home/ubuntu/day21_post_pipeline.py'], 'POST PIPELINE')

log('=== DAY21 MASTER RUN COMPLETE ===')
