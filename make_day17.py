#!/usr/bin/env python3
"""Generate the Day-17 (2026-10-31) pipeline scripts from the proven Day-16
versions by string substitution, then apply the Day-17 specific tweaks.

Rules that must survive the copy:
  - wave file / log names move to day17_*
  - the day tag moves to 'Daily 2026-10-31'
  - the wave runner must be able to run as 'day17_wave_runner.py' (the system
    crontab watchdog greps for that name)
  - the build script must score 2026-10-31 as the freshest date
"""
import os
import re

SRC = '/home/ubuntu'
PAIRS = [
    ('day16_wave_runner.py', 'day17_wave_runner.py'),
    ('day16_build_wave.py', 'day17_build_wave.py'),
    ('day16_site_verify.py', 'day17_site_verify.py'),
    ('day16_ig_hunt.py', 'day17_ig_hunt.py'),
    ('day16_ig_hunt_backlog.py', 'day17_ig_hunt_backlog.py'),
    ('day16_ig_pass.py', 'day17_ig_pass.py'),
    ('day16_post_pipeline.py', 'day17_post_pipeline.py'),
    ('day16_reply_sweep.py', 'day17_reply_sweep.py'),
    ('day16_verify.py', 'day17_verify.py'),
]

REPL = [
    ('day16_wave_runner.py', 'day17_wave_runner.py'),
    ('day16_build_wave.py', 'day17_build_wave.py'),
    ('day16_site_verify.py', 'day17_site_verify.py'),
    ('day16_ig_hunt.py', 'day17_ig_hunt.py'),
    ('day16_ig_hunt_backlog.py', 'day17_ig_hunt_backlog.py'),
    ('day16_ig_pass.py', 'day17_ig_pass.py'),
    ('day16_post_pipeline.py', 'day17_post_pipeline.py'),
    ('day16_reply_sweep.py', 'day17_reply_sweep.py'),
    ('day16_verify.py', 'day17_verify.py'),
    ('day16_wave.txt', 'day17_wave.txt'),
    ('day16_wave_detail.csv', 'day17_wave_detail.csv'),
    ('day16_site_verify.csv', 'day17_site_verify.csv'),
    ('day16_log.txt', 'day17_log.txt'),
    ('day16_ig_log.txt', 'day17_ig_log.txt'),
    ('day16_pipeline_log.txt', 'day17_pipeline_log.txt'),
    ('Daily 2026-10-30', 'Daily 2026-10-31'),
    ('Day-16 (2026-10-30)', 'Day-17 (2026-10-31)'),
    ('Day-13 (2026-10-27)', 'Day-17 (2026-10-31)'),
    ('Day-12 (2026-10-27)', 'Day-17 (2026-10-31)'),
    ("DAY = '2026-10-30'", "DAY = '2026-10-31'"),
    ("'2026-10-30' in st", "'2026-10-31' in st"),
    ("'2026-10-30' in st else", "'2026-10-31' in st else"),
    ('day16 QA', 'day17 QA'),
    ('day16 outreach 2026-10-30', 'day17 outreach 2026-10-31'),
    ('DAY16', 'DAY17'),
    ('day16', 'day17'),
]

for src, dst in PAIRS:
    p = os.path.join(SRC, src)
    txt = open(p, encoding='utf-8').read()
    for a, b in REPL:
        txt = txt.replace(a, b)
    out = os.path.join(SRC, dst)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(txt)
    print('wrote', dst)

# --- Day-17 specific tweak in the builder: fresh-date scoring must rank
#     2026-10-31 as the freshest (the Denver scrape landed this morning).
p = os.path.join(SRC, 'day17_build_wave.py')
txt = open(p, encoding='utf-8').read()
old = """    fresh = (4 if '2026-10-31' in st else 3 if '2026-10-29' in st
             else 2 if '2026-10-28' in st else 1 if '2026-10-27' in st
             else 1 if '2026-10-25' in st else 0)"""
new = """    fresh = (6 if '2026-10-31' in st else 4 if '2026-10-30' in st
             else 3 if '2026-10-29' in st else 2 if '2026-10-28' in st
             else 1 if '2026-10-27' in st else 1 if '2026-10-25' in st else 0)"""
if old in txt:
    txt = txt.replace(old, new)
    print('patched fresh-date scoring')
else:
    print('WARN: fresh-date scoring pattern not found -- inspect manually')

# --- Day-17 specific tweak in the IG pass: today's wave is day17 ---
p = os.path.join(SRC, 'day17_ig_pass.py')
txt = open(p, encoding='utf-8').read()
old = "fresh = 0 if r[0] in wave_ids else (1 if '2026-10-31' in st else 2)"
new = "fresh = 0 if r[0] in wave_ids else (1 if '2026-10-31' in st else 2)"
if old not in txt:
    print('WARN: ig_pass fresh-order pattern not found -- inspect manually')

open(p, 'w', encoding='utf-8').write(txt)
print('day17 script generation done')
