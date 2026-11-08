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
st = json.load(open('/home/ubuntu/company_reach_state.json')).get('processed', {})
todo = [(k, v) for k, v in h.items() if k not in st][:LIMIT]

ours = {}
theirs = {}
unknown = {}
print('screening %d companies against their own profile ...' % len(todo))
t0 = time.time()
for i, (k, v) in enumerate(todo, 1):
    prof = cr.curl(v.get('href') or '', timeout=22)
    buys = cr.buyer_wants(prof)
    verdict = cr.profile_verdict(buys)
    v['_buys'] = (buys or '')[:160]
    if verdict == 'ours':
        ours[k] = v
    elif verdict == 'theirs':
        theirs[k] = v
    else:
        unknown[k] = v
    if i % 25 == 0:
        print('  %d/%d | ours=%d theirs=%d unknown=%d (%.0fs)'
              % (i, len(todo), len(ours), len(theirs), len(unknown), time.time() - t0))

json.dump({'ours': ours, 'theirs': theirs, 'unknown': unknown},
          open(OUT, 'w'), indent=2, ensure_ascii=False)
print()
print('=== SCREENING RESULT ===')
print('  OURS (buys our products) : %d' % len(ours))
print('  UNKNOWN (no Buys phrase) : %d' % len(unknown))
print('  THEIRS (wrong product)   : %d' % len(theirs))
print()
print('=== our buyers ===')
for k, v in list(ours.items())[:30]:
    print('  %-40s | %-20s | %s' % (v['company'][:39], v.get('dir_country', ''),
                                   v['_buys'][:70]))
print()
print('=== the wrong-product ones we were about to chase ===')
for k, v in list(theirs.items())[:12]:
    print('  %-40s | %s' % (v['company'][:39], v['_buys'][:66]))
