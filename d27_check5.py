#!/usr/bin/env python3
"""D27: WA tab enumeration + last night's pipeline log + hot lead rows."""
import sys, time, json, csv, os, glob, re
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval

print('=== WA TAB ENUMERATION (never reload; test each tab) ===')
wa = [t for t in get_tabs() if 'web.whatsapp' in t.get('url','') and t['type']=='page']
print(' WA tabs found:', len(wa))
for i, t in enumerate(wa):
    try:
        ws = connect(t)
        v = js_eval(ws, """(() => {
          const t = document.body ? document.body.innerText : '';
          return JSON.stringify({qr: /Scan to log in|Log in to WhatsApp/i.test(t),
            pane: !!document.querySelector('#pane-side'),
            composer: !!document.querySelector('div[contenteditable="true"], textarea[data-tab="10"]'),
            head: t.replace(/\\s+/g,' ').slice(0,180)});
        })()""", await_promise=False)
        ws.close()
        print(f'  tab{i}:', str(v)[:300])
    except Exception as e:
        print(f'  tab{i}: ERR', str(e)[:90])

print()
print('=== LAST NIGHT PIPELINE LOG (20:00 UTC Oct 26 wave) ===')
cands = sorted(glob.glob('/home/ubuntu/*pipeline*.log') + glob.glob('/home/ubuntu/logs/*') +
               glob.glob('/home/ubuntu/*wave*.log'), key=os.path.getmtime, reverse=True)[:8]
for c in cands:
    print('---', c, time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(c))))
try:
    import subprocess
    out = subprocess.run(['bash','-lc','ls -lt /home/ubuntu/*.log /home/ubuntu/*.txt 2>/dev/null | head -12'],
                         capture_output=True, text=True).stdout
    print(out)
except Exception as e:
    print(e)

print('=== HOT LEAD ROWS (L964/L965) ===')
rows = list(csv.DictReader(open('/home/ubuntu/leads.csv', encoding='utf-8-sig')))
for r in rows:
    if (r.get('Lead ID') or '') in ('L964','L965'):
        print(' ', r.get('Lead ID'), '|', (r.get('Name') or '')[:40], '|', (r.get('Country') or '')[:14],
              '|', (r.get('Email') or '')[:30], '|', (r.get('Status') or '')[:70])

print()
print('=== WA send history by day (last 6 days) ===')
from collections import Counter
c = Counter()
for r in rows:
    st = (r.get('Status') or '')
    if re.search(r'whatsapp sent|WA sent', st, re.I) and 'not on WhatsApp' not in st and "isn't on WhatsApp" not in st:
        m = re.findall(r'2026-10-(\d\d)', st)
        if m: c[m[-1]] += 1
for k,v in sorted(c.items())[-6:]:
    print('  Oct', k, ':', v, 'WA')
