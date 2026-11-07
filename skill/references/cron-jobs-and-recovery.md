# Cron Jobs & Failure Recovery — HSN Warrior Apparels

Every scheduled job that touches the business, plus the rules that keep a
failed job from redoing work that already succeeded.

## Job inventory

| Job | ID | Schedule | Purpose |
|---|---|---|---|
| outreach-watchdog | `e443d3f0466b` | every 30m | restarts `worker.py` if dead (no_agent script) |
| nightly-git-backup | `8d87b574012b` | `0 2 * * *` | GitHub backup of leads/tracker/catalog (no_agent script) |
| morning-briefing | `f8b8d47f5151` | `0 0 * * *` | 5 AM PKT briefing → Telegram (`deliver=origin`) |
| daily-1am-outreach-pipeline | `22c8a5498741` | `0 20 * * *` | hunt + email wave + IG + WA + tracker + backup |
| gmaps-2pm-daily-scrape | `4e241a29f186` | `0 9 * * *` | 2 PM PKT Maps scrape + enrichment → Telegram |

- **Every business-work cron must deliver its report to the user's chat
  (`deliver=origin`).** The user reads local-only or cut-off delivery as
  withholding reports from him; if a fire's report gets cut short
  mid-monitoring, the 5 AM briefing must cover the gap.
- **Pin the absolute interpreter path in every cron/watchdog/kickoff script.**
  Bare `python3` under cron resolves to a different, dep-less interpreter and
  the worker crash-loops silently all night. After any kickoff, tail the worker
  log within a minute: a clean "Starting" line with no traceback. A
  start-then-crash loop still shows as "running" to `pgrep` — check the log,
  not the process list.
- System crontab (survives Hermes session ends): `csv_guard.sh` every 10 min
  (restores a 0-byte `leads.csv` from the git backup, logs to
  `/home/ubuntu/csv_guard.log` — check that log after any CSV anomaly);
  `wave_guard.sh` every 7 min (restarts a dead email-wave runner; the runner
  is resumable, so it never double-sends); `daily_automation_cron.sh` at
  `0 9 * * *`.

## The rule that prevents "it keeps starting from 0"

A provider error mid-run is NOT the real failure — **restarting from item 1
is.** The visible symptom ("you try this again and again and you start from
0") means the job re-does work it already completed.

1. **Make every per-item job re-entrant.** Mark each item durably the moment
   it completes (the wave runner writes `COMPLETE: email sent (<day>)` into
   `leads.csv` immediately after each send and skips marked rows on the next
   run). A job that only writes its result at the END cannot resume.
2. **Before re-running a failed job, establish what already succeeded.** Read
   the job's own log/state file and the tracker it writes, then re-run only
   what is genuinely missing. Re-running blind duplicates side effects —
   double-sends, duplicate records, a second email to a lead that already got
   one.
3. **Terminal states are terminal.** A lead marked sent / failed / excluded /
   re-hunt must never be picked up again by a guard or resume loop. Only
   genuinely PENDING work is re-queued.
4. **Use an exclusive lock** for any job that writes a shared file or drives
   one browser tab. Two runners on one Gmail tab race on `leads.csv` and
   double-send. Stale locks (owner PID gone) are reclaimed.
5. **Never hardcode a script filename in a cron prompt.** The pipeline
   advances (`dayNN_*.py`) and a prompt still pointing at an old script keeps
   firing while the real work silently stops happening. Reference the current
   script by a discoverable convention (newest `day*_wave_runner.py`) or
   update the prompt when the pipeline advances, and confirm the script the
   prompt names actually exists and is current.

## Provider failures inside a cron job

- **Route all NVIDIA calls through the shield** — see
  `references/nvidia-api-access.md`. A cron job that calls the provider
  directly both breaks on 429 and steals budget from every other job.
- **A 429 is not a reason to abandon the job.** Check the shield health
  (`curl -s http://127.0.0.1:8743/shield/health`) before assuming the limit
  changed: the account may simply be saturated by other work. The shield
  self-tunes and retries 429s inside the gate.
- **Prefer a no-agent script for deterministic work.** `no_agent: true` makes
  the script's stdout and exit code the whole job — no model tokens spent on a
  step a shell command does better, and the script's own log survives a model
  failure. Reserve the agent for the parts that need judgment (composing a
  briefing, deciding which leads to work).
- **Cron failures are recorded.** `hermes cron list` shows `last_status`,
  `last_error` and `failure_streak` per job; `hermes cron incidents` lists
  durable failure incidents. Check these before re-running anything.
- **Pause jobs before measuring the provider.** Concurrent jobs compete for
  the same account budget and make any measurement meaningless.
