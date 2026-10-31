#!/bin/bash
# Daily Automation Cron Wrapper
# Runs the full business automation pipeline

# Set up environment - USE HERMES PYTHON
export PATH="/home/ubuntu/.hermes/tools/python-3.14.7+202****0901-linux-arm64/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export HOME="/home/ubuntu"
export DISPLAY=":21"
export CDP_URL="http://localhost:9222"

# Change to working directory
cd /home/ubuntu

# Log start
echo "$(date): Starting daily automation" >> /home/ubuntu/daily_automation_cron.log

# Run the automation with timeout (4 hours max) - use hermes python
timeout 14400 /home/ubuntu/.hermes/tools/python-3.14.7+20260901-linux-arm64/bin/python3 daily_automation_full.py >> /home/ubuntu/daily_automation_cron.log 2>&1
EXIT_CODE=$?

# Log completion. Capture $? into a variable FIRST: `$(date)` inside the
# echo resets $? to the substitution's status, so the old one-liner always
# reported "exit code 0" no matter what actually happened.
echo "$(date): Daily automation completed with exit code $EXIT_CODE" >> /home/ubuntu/daily_automation_cron.log
if [ "$EXIT_CODE" -ne 0 ]; then
    echo "$(date): WARNING - daily automation FAILED (exit $EXIT_CODE)" >> /home/ubuntu/daily_automation_cron.log
fi

# Git backup (if git repo exists)
if [ -d .git ]; then
    git add -A >> /home/ubuntu/daily_automation_cron.log 2>&1
    git commit -m "Daily automation $(date +%Y-%m-%d)" >> /home/ubuntu/daily_automation_cron.log 2>&1
    git push >> /home/ubuntu/daily_automation_cron.log 2>&1
fi

echo "$(date): Git backup completed" >> /home/ubuntu/daily_automation_cron.log