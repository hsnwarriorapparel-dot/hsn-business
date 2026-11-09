"""Pre-screen the whole company pool with the go4WorldBusiness profile.

The directory CATEGORY is unreliable - a company listed under
'martial-arts-gloves' may say 'Buys industrial gloves, latex gloves'. The
member profile states what the buyer actually buys, so read it for every
remaining company and keep only the ones that buy OUR product.

Writes g4wb_company_screened.json with:
    ours    - buyers who want our products
    unknown - no 'Buys ...' sentence (worth trying)
    theirs  - confirmed wrong product (never search these again)
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, '/home/ubuntu')
import company_reach as cr

HARVEST = '/home/ubuntu/g4wb_company_harvest.json'
OUT = '/home/ubuntu/g4wb_company_screened.json'
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000

h = json.load(open(HARVEST))

# WHAT COUNTS AS "ALREADY SCREENED" IS THE SCREENED FILE, NOT THE REACH
# STATE. The old code skipped every company the reach campaign had
# marked 'processed' - but 'processed' means the company was CONTACTED,
# not that its profile was read. 330 companies had been contacted and
# never screened, and that pool held real buyers ('Buys karate belt',
# 'Buys uniforms like military uniform').
#
# The screen must therefore use its OWN output as the skip list.
try:
    _prev_raw = json.load(open(OUT))
except Exception:
    _prev_raw = {}
_already_screened = (set(_prev_raw.get('ours', {}))
                      | set(_prev_raw.get('theirs', {}))
                      | set(_prev_raw.get('unknown', {})))
todo = [(k, v) for k, v in h.items() if k not in _already_screened][:LIMIT]

# MERGE with the previous screening. The old code started from empty
# dicts and wrote only THIS run's todo, so every earlier verdict was
# wiped on each run - the file fell from 633 entries to 200.
prev = {}
try:
    prev = json.load(open(OUT))
except Exception:
    prev = {}
ours = dict(prev.get('ours', {}))
theirs = dict(prev.get('theirs', {}))
unknown = dict(prev.get('unknown', {}))
failed_fetch = {}
before = len(ours) + len(theirs) + len(unknown)
print('screening %d companies against their own profile ... '
      '(%d already screened, kept)' % (len(todo), before))
t0 = time.time()
for i, (k, v) in enumerate(todo, 1):
    prof = cr.curl(v.get('href') or '', timeout=22)
    buys = cr.buyer_wants(prof)
    verdict = cr.profile_verdict(buys)
    v['_buys'] = (buys or '')[:160]
    # A company belongs in EXACTLY ONE bucket. Re-screening it must
    # REPLACE the old verdict, not sit beside it - otherwise a company
    # that failed one fetch and succeeded the next appeared in both
    # 'ours' and 'unknown'.
    for bucket in (ours, theirs, unknown):
        bucket.pop(k, None)
    if verdict == 'ours':
        ours[k] = v
    elif verdict == 'theirs':
        theirs[k] = v
    elif buys:
        # it said something, but not something we make -> 'unknown'
        unknown[k] = v
    else:
        # NO 'Buys' sentence AND the fetch came back empty or without the
        # phrase. A profile that loads fine but states no product line is
        # a genuine unknown. A profile whose PAGE did not load is not -
        # it must stay retryable, so it is NOT written to the skip file.
        failed_fetch[k] = v
    if i % 25 == 0:
        print('  %d/%d | ours=%d theirs=%d unknown=%d (%.0fs)'
              % (i, len(todo), len(ours), len(theirs), len(unknown), time.time() - t0))

json.dump({'ours': ours, 'theirs': theirs, 'unknown': unknown},
          open(OUT, 'w'), indent=2, ensure_ascii=False)
# The retryable failures live in their OWN file so they are never written
# to the skip list and are picked up on the next run.
json.dump(failed_fetch, open('/home/ubuntu/g4wb_company_failed_fetch.json', 'w'),
          indent=2, ensure_ascii=False)
if failed_fetch:
    print('  %d profile(s) did not load - kept retryable, not filed as unknown'
          % len(failed_fetch))
print()
print('=== SCREENING RESULT ===')
print('  OURS (buys our products) : %d' % len(ours))
print('  UNKNOWN (no Buys phrase) : %d' % len(unknown))
print('  THEIRS (wrong product)   : %d' % len(theirs))
print('  TOTAL SCREENED           : %d' % (len(ours) + len(theirs) + len(unknown)))
print()
print('=== our buyers ===')
for k, v in list(ours.items())[:30]:
    print('  %-40s | %-20s | %s' % (v['company'][:39], v.get('dir_country', ''),
                                   v['_buys'][:70]))
print()
print('=== the wrong-product ones we were about to chase ===')
for k, v in list(theirs.items())[:12]:
    print('  %-40s | %s' % (v['company'][:39], v['_buys'][:66]))
