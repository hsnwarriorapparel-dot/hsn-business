# NVIDIA API Access — Rate Limits & Routing

Applies to EVERY tool, script, cron job, subagent and aux/vision client that
calls the NVIDIA API on this VPS.

## The published limit is NOT this account's limit

The docs say "40 RPM". Measured directly against this key: 429s at 8 RPM
(9 of 16 requests), 429s at 5 RPM (3 of 11), and a burst that 429'd on the
5th request. **The sustainable rate is ~3 successful RPM.** Never configure or
assume a rate above that.

Re-measure before changing anything — use the probe in the `hermes-agent`
skill: `scripts/probe-provider-ratelimit.py`. Do not trust a number quoted
from docs or from memory.

## All traffic goes through the central shield

The shield (`nvidia-shield.service`, systemd user unit) owns ONE shared
sliding-window cap for the whole account and self-tunes: it lowers its rate
on every 429 and raises it only after sustained clean responses.

| Setting | Value | How to set |
|---|---|---|
| `model.base_url` | `http://127.0.0.1:8743/v1` | `hermes config set model.base_url http://127.0.0.1:8743/v1` |
| `NVIDIA_BASE_URL` | `http://127.0.0.1:8743/v1` | `hermes_cli.config.save_env_value` |

Both are required. `model.base_url` covers the main agent runtime; the
`NVIDIA_BASE_URL` env var covers the aux/subagent/vision paths, which read the
env var and ignore `model.base_url`.

**NEVER point anything straight at `integrate.api.nvidia.com`.** That bypasses
the cap and is what produced the recurring "AI model service was rate-limited
(too many requests)" failures in cron jobs.

Health check: `curl -s http://127.0.0.1:8743/shield/health` reports
`rpm_current`, `rpm_ceiling`, `spacing_s` and `window_requests_last_60s`.

## Do NOT use the old per-process limiter for real calls

`/home/ubuntu/nvidia_rate_limiter.py` is an in-memory PER-PROCESS limiter.
The gateway, cron workers, delegated children and aux clients each get their
own 37-request budget while all charging the same account key, so it cannot
enforce an account-scoped limit — it was never imported by any real caller.
It is safe only for local mock / self-test traffic.

## Rules for any new tool or workflow calling NVIDIA

1. Route it through the shield URL. Do not open a direct client to NVIDIA.
2. If the script adds its own pacing on top, keep it BELOW the shield's
   current `rpm_current` — the shield is the authority.
3. After changing the shield, run `python3 /home/ubuntu/nvidia-shield/test_shield.py`
   (expect 12/12) and confirm `rpm_current` in the health output.
4. If a job dies with a 429, check the shield health BEFORE assuming the
   limit changed — the account may simply be saturated by other work.

## Editing Hermes config and secrets

- `~/.hermes/config.yaml` is write-protected from the agent. Always use
  `hermes config set KEY VALUE`; never patch the YAML.
- For `~/.hermes/.env`, use `hermes_cli.config.save_env_value` so the file
  stays parseable. Never print or log `.env` values — grep variable NAMES only.
- After changing either, the gateway must reload. A gateway cannot restart
  itself from inside a turn (it would kill its own session) — the user runs
  `hermes gateway restart` from a separate shell, or use the in-band
  `systemctl --user reload hermes-gateway` (SIGUSR1) which drains the current
  turn first.

## Why a per-process limiter fails (do not "simplify" this back)

Provider rate limits are ACCOUNT-scoped, not process-scoped. Hermes runs the
gateway, cron workers, delegated children and aux/vision clients as separate
processes, each with its own counter, all charged to one key. N processes x M
requests each still breaches a single account budget. The limit must be a
shared network gate every process routes through.
