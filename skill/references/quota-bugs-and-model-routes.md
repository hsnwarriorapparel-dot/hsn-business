# The 2026-11-06 pipeline failure and the three quota bugs

## The cron error was NOT a rate limit

The 1 AM cron reported:

```
HTTP 404: {"status":404,"title":"Not Found","detail":"Function 'e503b15c-...': Not found for account '...'"}
```

That is NVIDIA/route saying **the model function does not exist**, NOT a 429.
Telling them apart matters because the fixes are completely different.

Measured against the live API through the shield:

| Model | Result |
|---|---|
| `deepseek-ai/deepseek-coder-6.7b-instruct` | **404** |
| `nvidia/nemotron-3-super-120b-a12b` | **404** |
| `nvidia/llama-3.1-nemotron-ultra-253b-v1` | **404** |
| `minimaxai/minimax-m3.1-flash` | **200** |
| `nvidia/nemotron-3-ultra-550b-a55b` | **200** |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | **200** |
| `deepseek-ai/deepseek-v4.1-flash` | **200** |

The primary provider `agentrouter.org` was also returning **401** on
`/v1/models` ("unauthorized client detected"). So the whole chain was dead:
primary 401, both fallbacks 404.

**Fix (always via the CLI, never hand-edit config.yaml):**
```bash
hermes config set model.provider nvidia
hermes config set model.base_url http://127.0.0.1:8743/v1
hermes config set model.default minimaxai/minimax-m3.1-flash
hermes config set fallback_providers '[{"provider":"nvidia","model":"nvidia/nemotron-3-ultra-550b-a55b"},{"provider":"nvidia","model":"deepseek-ai/deepseek-v4.1-flash"}]'
```

**Always TEST every candidate model with a real chat/completions call before
installing it.** A model appearing in `/v1/models` does NOT mean it can be
called - the catalog lists models the account cannot route to.

## THE STRUCTURAL FIX: cron jobs must not need a model

The 1 AM pipeline was an AGENT job whose prompt said "run the launcher". That
meant the entire night's outreach depended on a model call succeeding. When
the route died, it failed **before sending a single email** and the day's work
was silently skipped.

Every business cron is now `no_agent: true` with a script:
- `daily-1am-outreach-pipeline` -> `daily_outreach_pipeline.sh`
- `chain-franchise-corporate-pitch` -> `chain_pitch_daily.sh`
- `daily-followup-email-wave` -> `followup_daily.sh`
- plus morning-briefing, gmaps scrape, git backup, watchdog (already script)

**A script-only cron cannot fail on a model error, a 429, or a dead route.**

## Three quota bugs, all the same root cause

All three came from matching a DATE against the whole Status string, so the
lead-source stamp `HUNTED (gmaps 2PM <date>)` counted as an outreach action.

1. **Hardcoded day tag.** `day23_wave_runner.py` was copied from day22 with
   `DAY = 'Daily 2026-11-05'` still in it. The runner counted day22's 100
   emails as "already sent today" and refused to send anything on a day with
   0 sends (Gmail confirmed 0). Symptom: the wave log shows
   `QUOTA: 100 sent today ... allowance 0` on a fresh day.
   **Fix:** read the date from `dayNN_quota_state.json`; never a literal.

2. **Substring date match.** `if DAY in _st and 'email sent' in _st` counts
   a row whose Status is `HUNTED (gmaps 2PM 2026-11-06)`. Same bug class as
   the `hsn_counters.py` "today" block fixed earlier.
   **Fix:** a row counts only when the SAME marker carries both the action
   and the day tag:
   ```python
   for part in status.split('|'):
       if 'email sent' in part.lower() and DAY in part:
           count += 1
           break
   ```

3. **Quota computed once at startup.** Two runners ran concurrently - the
   system-crontab `wave_guard.sh` runner (every 7 min) and the orchestrator's
   own runner. Both computed `allowance 100` at the same moment, so the day
   went to 101/100.
   **Fix:** re-read the CSV and re-check the quota **before every send**.
   ```python
   live = count_rows_with_today_markers()   # fresh read from disk
   if live >= DAILY_EMAIL_QUOTA:
       break                              # remaining stay queued
   ```
   Verified afterwards: 101 sends, 101 unique lead IDs, **zero duplicates** -
   the lock had already prevented a double-send, only the COUNT was wrong.

   The same per-send re-check belongs in every sender: first-touch wave,
   follow-up engine, chain pitches.

## The `wave_guard.sh` interaction

`wave_guard.sh` runs every 7 minutes from the SYSTEM crontab and restarts the
wave runner if it dies. It resolves the day tag dynamically (`--day "$TAG"`),
so it is quota-safe. But it means **two wave runners can be alive at once**
whenever the orchestrator starts its own pass. That is fine for duplicate
prevention (the wave lock + per-lead `email sent` markers handle it) but it
breaks any quota count that is not re-read live.

## Ammo top-up is now automatic

Ammo fell to 20 (target 100), so a night produced a 20-email wave.
`dayNN_run.py` now counts ammo BEFORE building the wave and runs
`dayNN_ammo_hunt.py` when it is short. The hunt covers FRESH EU markets:
Athens, Thessaloniki, Warsaw, Krakow, Vienna, Graz, Copenhagen, Brussels,
Antwerp, Ljubljana, Zagreb, Budapest - countries holding 0-29 leads each while
USA holds 1807.

**Never hardcode dates in the day scripts** - `dayNN_precheck.py` had
`TODAY = '2026/11/05'` which reported the wrong Gmail ground truth the next
day. Compute them:
```python
_today = datetime.datetime.now(datetime.timezone.utc).date()
TODAY = _today.strftime('%Y/%m/%d')
YESTERDAY = (_today - datetime.timedelta(days=1)).strftime('%Y/%m/%d')
```
