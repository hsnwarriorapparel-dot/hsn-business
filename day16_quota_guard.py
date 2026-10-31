#!/usr/bin/env python3
"""Quota guard for Day-16 (2026-10-30).

A legacy day6_pipeline.py fired 3x at 07:21-07:32 UTC today from a stale
session and sent 13 REAL emails, all tagged 'email sent (Daily 2026-10-30)'.
The user's hard quota is 100 emails/day, so today's wave must stop at
87 sends (13 + 87 = 100).

This watcher polls the wave log and kills the wave runner the moment it
reaches position 87, so the day ends at exactly 100 emails.

Wave file position 1 (L2745) was already sent by the foreground test, so
positions 1..87 = 87 sends from this wave.
"""
import os, re, time, subprocess, signal

LOG = '/home/ubuntu/day16_log.txt'
TARGET_POS = 87
PAT = 'day16_wave_runner.py'

print(f'quota guard: will stop wave at position {TARGET_POS} (13 pre-existing + {TARGET_POS} = 100)', flush=True)

while True:
    time.sleep(5)
    try:
        txt = open(LOG, errors='replace').read()
    except Exception:
        continue
    poss = [int(m) for m in re.findall(r'\[(\d+)/100\]', txt)]
    last = max(poss) if poss else 0
    if last >= TARGET_POS:
        # give the current send a moment to finish its CSV marker write
        time.sleep(45)
        out = subprocess.run(['ps', '-eo', 'pid,cmd'], capture_output=True, text=True).stdout
        killed = []
        for line in out.splitlines():
            if PAT in line and 'python3' in line and 'grep' not in line:
                pid = int(line.split()[0])
                if pid == os.getpid():
                    continue
                try:
                    os.kill(pid, signal.SIGTERM)
                    killed.append(pid)
                except Exception:
                    pass
        print(f'quota guard: reached position {last}; killed wave runner pids {killed}', flush=True)
        # final tally
        sent = len(re.findall(r'\[(\d+)/100\][^\n]*: OK', txt))
        skipped = len(re.findall(r'SKIP ', txt))
        print(f'quota guard: wave OK lines={sent} skips={skipped}', flush=True)
        break
    if last:
        print(f'quota guard: at position {last}/{TARGET_POS}', flush=True)
