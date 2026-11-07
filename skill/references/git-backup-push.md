# Git Backup to GitHub — the push that silently failed

`/home/ubuntu/.hermes/scripts/backup-git.sh` (nightly cron 8d87b574012b, 2:00 UTC)
backed up leads.csv + tracker + scripts to `github.com/hsnwarriorapparel-dot/hsn-business`.

## The bug that hid for weeks (found 2026-11-05)

The script set `GIT_SSH_COMMAND=...` as a **plain shell assignment, never
`export`ed** it. A shell variable that is not exported is NOT inherited by
child processes, so `git push` never saw it and fell back to the keys offered
by `SSH_AUTH_SOCK` (a gpg-agent on this box) — which GitHub does not accept:

```
git@github.com: Permission denied (publickey).
fatal: Could not read from remote repository.
```

Two things made it invisible:
1. The script echoed **"backup pushed to github.com/..."** unconditionally,
   AFTER the failed push. The log said success every single night.
2. The cron job reported `last_status: ok` — the script's exit code was 0
   because the `echo` was the last command.

Meanwhile a MANUAL push worked, because an interactive shell exports
`GIT_SSH_COMMAND`. So the symptom was "manual works, cron doesn't" — which
looks like a flaky network or a key problem, not a missing `export`.

## How to spot this class of bug

When a command works manually but fails in a script, diff the ENVIRONMENT, not
just the arguments. A shell assignment without `export` is invisible to every
child process. Quick check:

```bash
grep -n 'GIT_SSH_COMMAND' script.sh          # is it exported?
bash -c 'VAR=x; env | grep VAR'               # -> VAR is MISSING
bash -c 'export VAR=x; env | grep VAR'        # -> VAR=x
```

## The correct pattern

```bash
export GIT_SSH_COMMAND="ssh -i /home/ubuntu/.ssh/hsn_backup_key -o IdentitiesOnly=yes -o StrictHostKeyChecking=no"
```

- `export` — REQUIRED, otherwise git never sees it.
- `-o IdentitiesOnly=yes` — stops ssh offering the gpg-agent's keys first.
- `-o StrictHostKeyChecking=no` — avoids a host-key prompt in a headless cron.

## Verify the push, never assume it

```bash
cd /home/ubuntu/business-backup
git status -sb | head -2        # "ahead N" means the push DID NOT land
git rev-parse HEAD
GIT_SSH_COMMAND='ssh -i /home/ubuntu/.ssh/hsn_backup_key -o IdentitiesOnly=yes' git ls-remote origin main
```

Local HEAD and the remote SHA must match. `ahead N` = the backup is NOT on
GitHub.

## Report the real result

The fixed script checks the push exit code and prints
`BACKUP PUSH FAILED (rc=...)` with the re-run command, and exits non-zero so
the cron records the failure. Never echo "backup pushed" unconditionally.

## Python equivalents

Python scripts must pass the env explicitly — a plain dict assignment is not
inherited either:

```python
env = dict(os.environ)
env['GIT_SSH_COMMAND'] = 'ssh -i /home/ubuntu/.ssh/hsn_backup_key -o IdentitiesOnly=yes'
subprocess.run(['git', 'push', 'origin', 'main'], env=env, ...)
```

`gmaps_daily_scrape.py` sets it inline inside the shell command it runs
(`GIT_SSH_COMMAND='...' git push origin main`), which is also correct —
that form is scoped to that one command.
