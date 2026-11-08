#!/usr/bin/env python3
"""Report on the go4WorldBusiness buyer-directory funnel."""
import csv
import json
import re
from collections import Counter

CSV_PATH = '/home/ubuntu/leads.csv'
# The live harvest files. The legacy shared file is NOT counted - it is the
# old pre-split snapshot and counting it made the report show stale numbers
# (811 identities / 60 filtered instead of 1662 / 212).
RAW_FILES = ['/home/ubuntu/g4wb_buyer_harvest_dir.json',
             '/home/ubuntu/g4wb_buyer_harvest_search.json']
RAW = None
COMPANIES = '/home/ubuntu/g4wb_company_harvest.json'
FILT = '/home/ubuntu/g4wb_buyer_harvest_filtered.json'
STATE = '/home/ubuntu/buyer_reach_state.json'
QUEUE = '/home/ubuntu/g4wb_buyer_queue.json'
QSTATE = '/home/ubuntu/g4wb_buyer_queue_state.json'


def jload(p, d):
    try:
        return json.load(open(p))
    except Exception:
        return d


raw = {}
for f in RAW_FILES:
    for k, v in jload(f, {}).items():
        raw.setdefault(k, v)
companies = jload(COMPANIES, {})
filt = jload(FILT, {})
reach = jload(STATE, {'processed': {}}).get('processed', {})
# the COMPANY funnel has its own state file
CREACH = '/home/ubuntu/company_reach_state.json'
creach = jload(CREACH, {'processed': {}}).get('processed', {})
queue = jload(QUEUE, [])
qstate = jload(QSTATE, {})

added = sum(1 for v in reach.values() if v.get('status') == 'added')
nomatch = sum(1 for v in reach.values() if v.get('status') == 'no-match')
dup = sum(1 for v in reach.values() if v.get('status') == 'duplicate')
c_added = sum(1 for v in creach.values() if v.get('status') == 'added')
c_nomatch = sum(1 for v in creach.values() if v.get('status') == 'no-match')
c_dup = sum(1 for v in creach.values() if v.get('status') == 'duplicate')
c_junk = sum(1 for v in creach.values() if v.get('status') == 'junk-name')

# how many of the new leads are in leads.csv
new_ids = [v.get('lead') for v in reach.values() if v.get('status') == 'added']
live = 0
try:
    with open(CSV_PATH, newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if r.get('Lead ID') in new_ids:
                live += 1
except Exception:
    pass

print('=== go4WorldBusiness buyer-directory funnel ===')
print('  buyer COMPANIES harvested      : %d' % len(companies))
print('  raw buyer identities harvested : %d' % len(raw))
print('  filtered to our product space  : %d' % len(filt))
print()
print('  -- by company name (the strong funnel) --')
print('  searched for a company         : %d' % len(creach))
print('    -> company + email/phone     : %d' % c_added)
print('    -> already in tracker        : %d' % c_dup)
print('    -> no match                  : %d' % c_nomatch)
print('    -> junk name skipped         : %d' % c_junk)
print()
print('  -- by personal name (the weak funnel) --')
print('  searched for a person          : %d' % len(reach))
print('    -> company + email found     : %d' % added)
print('    -> already in tracker        : %d' % dup)
print('    -> no match                  : %d' % nomatch)
print()
print('=== platform inquiry slot (1/day) ===')
print('  sent today                     : %s' % qstate.get('sent_today_count', 0))
print('  last inquiry                   : %s (%s)' % (qstate.get('last_slug', '-'),
                                                      qstate.get('last_result', '-')))
print('  queued RFQs waiting            : %d' % sum(1 for q in queue if not q.get('sent')))
top = [q for q in queue if not q.get('sent')][:4]
for q in top:
    print('     %-44s %-16s %s' % (q.get('slug', '')[:43], (q.get('qty') or '')[:15],
                                  q.get('buyer', '')))
print()
print('  NOTE: the directory funnel is NOT limited by the 1/day platform slot.')
print('  The platform slot is one extra channel; the directory is the volume one.')
