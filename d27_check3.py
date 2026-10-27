#!/usr/bin/env python3
"""D27: go4WorldBusiness verification body + newest human Gmail replies + IG DM inbox."""
import sys, time, json, re
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

PERSONAL = re.compile(r'sayyam|shamas|afzal|chacho', re.I)

gm = [t for t in get_tabs() if 'mail.google' in t.get('url','') and t['type']=='page'][0]
ws = connect(gm)
cdp = make_cdp(ws)

print('=== go4WorldBusiness verification result (open thread) ===')
cdp('Page.navigate', {'url': 'https://mail.google.com/mail/u/0/#search/from%3Amarco%40go4worldbusiness.com+OR+subject%3A%22verification%22'})
time.sleep(8)
js_eval(ws, """(() => {
  const rows = Array.from(document.querySelectorAll('tr'));
  for (const r of rows) {
    const t = (r.innerText||'');
    if (t.includes('erification')) { r.click(); return 'clicked'; }
  }
  return 'noclick';
})()""", await_promise=False)
time.sleep(8)
v = js_eval(ws, """(() => {
  const main = document.querySelector('div[role="main"]');
  return JSON.stringify(main ? (main.innerText||'').replace(/\\s+/g,' ').slice(0,2000) : 'nomain');
})()""", await_promise=False)
print(str(v)[:2100])

print()
print('=== NEWEST inbound human mail (newer_than:3d, unread, not auto-ack) ===')
cdp('Page.navigate', {'url': 'https://mail.google.com/mail/u/0/#search/newer_than%3A3d+-from%3Ame+is%3Aunread'})
time.sleep(8)
v2 = js_eval(ws, """(() => {
  const rows = Array.from(document.querySelectorAll('tr')).slice(0,30);
  const out = [];
  for (const r of rows) {
    const spans = Array.from(r.querySelectorAll('span[email]'));
    const from = spans.length ? (spans[0].getAttribute('email')||'') : '';
    const txt = (r.innerText||'').replace(/\\s+/g,' ').slice(0,220);
    if (from) out.push({from: from, txt: txt});
  }
  return JSON.stringify(out);
})()""", await_promise=False)
try:
    items = json.loads(v2)
    print(' unread rows with sender:', len(items))
    for it in items:
        if PERSONAL.search(it['from']): continue
        print('  *', it['from'], '||', it['txt'][:160])
except Exception as e:
    print(' parse err', str(e)[:100], str(v2)[:300])
ws.close()

print()
print('=== IG DM INBOX ===')
igt = [t for t in get_tabs() if 'instagram.com' in t.get('url','') and t['type']=='page']
if igt:
    ws2 = connect(igt[0])
    cdp2 = make_cdp(ws2)
    cdp2('Page.navigate', {'url': 'https://www.instagram.com/direct/inbox/'})
    time.sleep(9)
    v3 = js_eval(ws2, """(() => {
      const t = document.body ? document.body.innerText : '';
      const login = /Log in to Instagram|accounts\\/login/i.test(location.href) || /Log in to Instagram/i.test(t);
      return JSON.stringify({login: login, head: t.replace(/\\s+/g,' ').slice(0,1400)});
    })()""", await_promise=False)
    ws2.close()
    print(str(v3)[:1500])
