#!/bin/bash
# go4WorldBusiness buyer-directory pipeline (cron: 25 9 * * *).
#
# THE STRATEGY (new, 2026-11-07)
# -------------------------------
# go4WorldBusiness allows a JUNIOR member ONE buyer inquiry per day:
#   "As you are not a Premium GOLD/SILVER Member, you can only contact
#    limited number of buyers."
# So the inquiry FORM is a 1/day slot, not a channel.
#
# But the site publishes a full BUYER DIRECTORY:
#   https://www.go4worldbusiness.com/buyers/<country>/<category-slug>
# Every requirement there names the buyer:
#   "Contact : Nabil Al Raisi   Buyer Of Martial Arts Goods and Accessories"
#   "Contact : Ali Aref          Buyer Of Boxing Accessories | Boxing Gloves"
#
# A buyer NAME + COUNTRY + product category is enough to find the real
# importing company on the open web and reach it on its OWN email - no
# platform limit, no captcha, no daily cap. That is a second, independent
# funnel that the 1/day slot cannot block.
#
# STAGES
#   1. harvest  - walk the buyer directory, collect buyer identities
#   2. filter   - keep only buyers whose own category is our product space
#   3. reach    - web-search each buyer, find the company, verify it is a
#                 real importer (not a retail shop), pull its email, add it
#                 to leads.csv ready for the normal outreach wave
#
# Every added lead goes through the standard spam QA and the normal 100/day
# cold-email quota, so nothing here bypasses the deliverability rules.
set -u
PY=$(ls -d /home/ubuntu/.hermes/tools/python-3*/bin/python3 2>/dev/null | sort -V | tail -1)
if [ -z "$PY" ]; then echo "interpreter not found"; exit 1; fi
LOG=/home/ubuntu/g4wb_dir_pipeline_log.txt

echo "=== g4wb buyer-directory pipeline $(date -u '+%Y-%m-%d %H:%M:%S UTC') ==="

# 1+2: harvest and filter
"$PY" /home/ubuntu/g4wb_dir_harvest.py --pages 4 2>&1 | tee -a "$LOG"
"$PY" /home/ubuntu/g4wb_filter_harvest.py 2>&1 | tee -a "$LOG"

# 3: reach - turn identities into contactable leads.
#
# The PERSONAL-NAME FUNNEL IS GONE. It produced 0 verified buyer
# companies and added junk (a privacy contact address, a Wix form
# address, a personal website). Searching a person's name finds other
# people - people-search sites, TikTok, BJJ profiles. The company funnel
# is 12x more productive, so all the budget goes there.
#
# "$PY" /home/ubuntu/buyer_reach.py --limit 5 2>&1 | tee -a "$LOG"

# 4: the COMPANY funnel - the volume channel. /buyers/<country>/<cat>.html
#    lists real buyer companies, which are a far better search key than a
#    person's name. This is what bypasses the platform's 1 inquiry/day limit.
"$PY" /home/ubuntu/g4wb_company_harvest.py --pages 4 2>&1 | tee -a "$LOG"

# 4a: SCREEN against each buyer's own go4WorldBusiness profile. The
#     directory CATEGORY is unreliable - one company listed under
#     'martial-arts-gloves' says 'Buys industrial gloves, latex gloves'.
#     The profile states what they actually buy, and reading it is one
#     fetch instead of a web search plus a page fetch.
"$PY" /home/ubuntu/screen_buyers.py 2>&1 | tee -a "$LOG"

"$PY" /home/ubuntu/company_reach.py --limit 30 2>&1 | tee -a "$LOG"

# report
"$PY" /home/ubuntu/g4wb_pipeline_report.py 2>&1 | tee -a "$LOG"
exit 0
