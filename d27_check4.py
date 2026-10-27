#!/usr/bin/env python3
"""D27 final: IG inbound replies + USA wave status + bounce stats from CSV."""
import sys, time, json, csv, re
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

print('=== IG INBOUND (not "You:") ===')
igt = [t for t in get_tabs() if 'instagram.com/direct' in t.get('url','') and t['type']=='page']
if igt:
    ws = connect(igt[0])
    cdp = make_cdp(ws)
    cdp('Page.navigate', {'url': 'https://www.instagram.com/direct/inbox/'})
    time.sleep(9)
    v = js_eval(ws, """(() => {
      const t = document.body ? document.body.innerText : '';
      const rows = Array.from(document.querySelectorAll('div[role="listitem"], li, a[href*="/direct/t/"]'));
      const out = [];
      const seen = new Set();
      for (const r of rows) {
        const txt = (r.innerText||'').replace(/\\s+/g,' ').trim();
        if (!txt || seen.has(txt)) continue;
        seen.add(txt);
        out.push(txt.slice(0,220));
      }
      return JSON.stringify({n: out.length, items: out.slice(0,25), head: t.replace(/\\s+/g,' ').slice(0,600)});
    })()""", await_promise=False)
    ws.close()
    try:
        d = json.loads(v)
        print(' rows:', d.get('n'))
        for it in d.get('items', []):
            print('  -', it[:200])
    except Exception as e:
        print(' raw:', str(v)[:900])

print()
print('=== CSV STATUS ANALYSIS ===')
rows = list(csv.DictReader(open('/home/ubuntu/leads.csv', encoding='utf-8-sig')))
print(' total rows:', len(rows))
usa = [r for r in rows if (r.get('Country') or '').strip().lower() in ('usa','united states','us','united states of america')]
print(' USA rows:', len(usa))
def has(r, s): return s.lower() in (r.get('Status') or '').lower()
usa_email = [r for r in usa if has(r,'email sent')]
usa_ig = [r for r in usa if has(r,'ig follow') or has(r,'dm=sent')]
usa_wa = [r for r in usa if has(r,'whatsapp sent') or has(r,'wa sent')]
print('  USA email sent:', len(usa_email), '| USA ig done:', len(usa_ig), '| USA wa sent:', len(usa_wa))
print('  USA with email addr:', len([r for r in usa if (r.get('Email') or '').strip()]))
print('  USA statuses sample:', sorted(set((r.get('Status') or '')[:38] for r in usa))[:12])
print()
print('=== ALL-TIME bounce/FAIL analysis (last 3 days by note/date) ===')
from collections import Counter
fail = [r for r in rows if 'FAILED' in (r.get('Status') or '') or 'Delivery' in (r.get('Status') or '')]
print(' rows with FAILED/Delivery status:', len(fail))
print(' sample:', [(r.get('Lead ID'), (r.get('Name') or '')[:24], (r.get('Status') or '')[:52]) for r in fail[:8]])
print()
print('=== recent daily counts (status contains HUNTED markers) ===')
c = Counter()
for r in rows:
    st = (r.get('Status') or '')
    m = re.search(r'HUNTED \(([^)]*)\)', st)
    if m: c[m.group(1)] += 1
for k,v in list(c.most_common())[-6:]:
    print('  ', k, v)
