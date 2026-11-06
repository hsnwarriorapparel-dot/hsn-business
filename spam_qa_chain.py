import sys, json
sys.path.insert(0, '/home/ubuntu')
from spam_qa_followup import check

d = json.load(open('/home/ubuntu/day23_chain_pitches.json'))
bad = 0
for p in d:
    hits = check(p['subject'] + '\n' + p['body'], p['brand'])
    print('%-24s %s' % (p['brand'], 'OK' if not hits else 'FLAG'))
    for k, t in hits:
        print('      %-7s %r' % (k, t))
    if hits:
        bad += 1
print()
print('FAIL' if bad else 'PASS - all chain copy clears the spam-word-checker')
sys.exit(1 if bad else 0)
