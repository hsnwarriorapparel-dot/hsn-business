#!/bin/bash
# Restart worker if it died
if ! pgrep -f "/home/ubuntu/.hermes/tools/python-3.14.7+20260901-linux-arm64/bin/python3 /home/ubuntu/worker.py" > /dev/null; then
    if [ -f /home/ubuntu/worker_restart.lock ]; then
        exit 0
    fi
    cd /home/ubuntu && { /home/ubuntu/.hermes/tools/python-3.14.7+20260901-linux-arm64/bin/python3 /home/ubuntu/worker.py >> worker_stdout.txt 2>&1 & }
fi
