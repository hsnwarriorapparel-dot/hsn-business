# Cron Jobs — Must Resume, Never Restart From Zero

The HSN cron jobs run unattended overnight. Two rules make them survive a
provider rate limit or a dead session without losing work.

## Rule 1 — script-only jobs make NO model calls

A cron job that needs the model for its actual work will die when the provider
is rate-limited, and the retry rebuilds everything from zero. So every job's
*work* lives in a script, and the cron either runs the script directly
(`no_agent: true`) or runs it as step one of a short agent turn.

| Job | Script | Model calls |
|---|---|---|
| `morning-briefing` (f8b8d47f5151) | `~/.hermes/scripts/morning-briefing.sh` -> `morning_briefing_collect.py` | none (no_agent) |
| `gmaps-2pm-daily-scrape` (4e241a29f186) | `~/.hermes/scripts/gmaps-daily-scrape.sh` -> `gmaps_daily_scrape.py` | none (no_agent) |
| `daily-1am-outreach-pipeline` (22c8a5498741) | `run_today_outreach.py` -> `dayNN_run.py` | only for the final report |

The morning briefing and the gmaps scrape used to be agent jobs. Both failed
with HTTP 429 *after* their scripts had already done the work successfully —
the failure was purely the summary/delivery step.

## Rule 2 — the outreach pipeline resolves TODAY's scripts itself

The pipeline cron prompt used to hardcode `day6_pipeline.py` (a 2026-10-19
script) while the real work lived in `dayNN_*.py` files hand-edited every
night. The prompt went stale and the agent had to guess.

**`/home/ubuntu/run_today_outreach.py` is the only entry point.** It:
- picks the newest `dayNN_*` family on disk (no hardcoded day number)
- reads the day tag from `dayNN_quota_state.json`
- takes an exclusive lock so a retry never races the original
- is resumable: the wave runner marks each lead `email sent` in
  `leads.csv` the instant it succeeds, so re-running continues where it
  stopped and never double-sends
- reports `--status`: wave pending count, ammo count, whether a pipeline is
  alive

```bash
python3 /home/ubuntu/run_today_outreach.py --status   # inspect, run nothing
python3 /home/ubuntu/run_today_outreach.py             # run / resume
```

If a pipeline dies, run it again — it resumes. Never hand-write a wave and
never run `day6_pipeline.py` (obsolete).

## Rule 3 — never work around a 429

When a job dies with HTTP 429, the provider is saturated. Waiting and letting
the shield throttle is the correct behaviour. Do NOT:
- point the job back at `integrate.api.nvidia.com`
- start a second copy of the job to "get more done"
- raise the shield's RPM ceiling

See `references/nvidia-api-access.md` for the measured limits.

## Rule 4 — verify with ground truth, not logs

`leads.csv` Status markers are written by the agent's own scripts, and a
script can mark a row it did not actually send. The authoritative check is
Gmail itself:

```python
from gmail_counter import GmailCounter
g = GmailCounter()
print(g.count('in:sent after:2026/11/04'))
g.close()
```

Hash-URL navigation silently fails (the query never applies); the counter
types into the real Search-mail input, which works. Report the Gmail number.
