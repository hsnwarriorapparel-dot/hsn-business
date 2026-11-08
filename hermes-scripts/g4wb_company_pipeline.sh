#!/bin/bash
# Standalone company funnel - now a thin wrapper around the cron pipeline.
#
# There used to be TWO scripts that both ran company_reach.py:
#   this one (--limit 30) and g4wb_dir_pipeline.sh (--limit 20).
# Running both wasted hours on the same Omani companies and produced
# duplicate candidates (the same junk site under two different names).
#
# One funnel, one runner. This wrapper calls the cron pipeline.
set -u
exec bash /home/ubuntu/.hermes/scripts/g4wb_dir_pipeline.sh
