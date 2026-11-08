#!/bin/bash
# Nightly business backup to GitHub - 2:00 AM UTC every day
BACKUP_DIR="/home/ubuntu/business-backup"
WEB_DIR="/home/ubuntu/mibro-website-v3"
# IdentitiesOnly=yes keeps ssh from offering the gpg-agent's keys first.
# export is REQUIRED: a plain shell assignment is NOT inherited by child
# processes, so git never saw GIT_SSH_COMMAND, fell back to the agent's keys,
# and every nightly push failed with "Permission denied (publickey)" while a
# manual push (where the var was exported) succeeded. This made the repo
# silently fall behind with the log still claiming "backup pushed".
export GIT_SSH_COMMAND="ssh -i /home/ubuntu/.ssh/hsn_backup_key -o IdentitiesOnly=yes -o StrictHostKeyChecking=no"

# Refresh the backup folder
mkdir -p "$BACKUP_DIR"
# WA_Pending_List.xlsx belongs here too: the post-pipeline copies it, but that
# step can be killed by a timeout before it runs, which left the file stale in
# the repo. The nightly backup must cover every generated artefact.
cp -u /home/ubuntu/leads.csv /home/ubuntu/HWA_Lead_Tracker.xlsx /home/ubuntu/HSN_Warrior_Apparels_Catalog.pdf /home/ubuntu/HSN_Price_List.pdf /home/ubuntu/business-backup/ 2>/dev/null
cp -u /home/ubuntu/WA_Pending_List.xlsx /home/ubuntu/business-backup/ 2>/dev/null
cp -u /home/ubuntu/*.py /home/ubuntu/business-backup/ 2>/dev/null
# The skill directory holds EVERY hard-won rule (outreach protocols, price
# list, brand traps, client-reply handling, go4WorldBusiness form mechanics).
# It was NOT in the repo, so a lost VPS would lose the business knowledge
# base entirely. Sync it too.
mkdir -p "$BACKUP_DIR/skill"
cp -ru /home/ubuntu/.hermes/skills/hsn-business-hub/. "$BACKUP_DIR/skill/" 2>/dev/null
# The .hermes/scripts directory holds the NIGHTLY PIPELINE, the watchdog
# and the cron wiring. It was NOT in the repo, so a lost VPS would lose the
# automation itself - the tracker and the knowledge base would survive but
# nothing would run them. Sync it too.
mkdir -p "$BACKUP_DIR/hermes-scripts"
cp -ru /home/ubuntu/.hermes/scripts/. "$BACKUP_DIR/hermes-scripts/" 2>/dev/null
# The cron job definitions drive the schedule. Back them up as well -
# but only the DEFINITIONS, not the runtime state. The lock files, the
# delivery/execution databases and the logs are live runtime artefacts
# that change every tick; copying them makes every backup dirty and
# adds noise without protecting anything.
mkdir -p "$BACKUP_DIR/hermes-cron"
cp -ru /home/ubuntu/.hermes/cron/jobs.json "$BACKUP_DIR/hermes-cron/" 2>/dev/null
for f in /home/ubuntu/.hermes/cron/*.json; do
  [ -e "$f" ] || continue
  b=$(basename "$f")
  [ "$b" = "jobs.json" ] && continue
  cp -u "$f" "$BACKUP_DIR/hermes-cron/" 2>/dev/null
done

# Sync website source (only changed files)
cd /home/ubuntu/business-backup
cd website-source 2>/dev/null || mkdir -p website-source
cp -u "$WEB_DIR"/*.html "$WEB_DIR/styles.css" "$WEB_DIR/assets/img/"* "$BACKUP_DIR/website-source/" 2>/dev/null

# Git commit & push (only if something changed)
cd /home/ubuntu/business-backup
git add -A
if git diff --cached --quiet; then
    echo "$(date -u '+%Y-%m-%d %H:%M UTC') — nothing changed, no backup needed"
    exit 0
fi
git commit -m "Auto-backup $(date -u '+%Y-%m-%d %H:%M UTC')

Files backed up:
$(git diff --cached --name-only)"

# Report the push RESULT. The old version echoed "backup pushed" regardless
# of the exit code, so a failed push looked successful in the log while the
# repo silently stayed behind.
if git push origin main; then
    echo "$(date -u '+%Y-%m-%d %H:%M UTC') — backup pushed to github.com/hsnwarriorapparel-dot/hsn-business"
    exit 0
else
    RC=$?
    echo "$(date -u '+%Y-%m-%d %H:%M UTC') — BACKUP PUSH FAILED (rc=$RC). Commit exists locally; re-run: cd /home/ubuntu/business-backup && git push origin main" >&2
    exit $RC
fi
