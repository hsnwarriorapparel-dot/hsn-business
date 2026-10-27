#!/usr/bin/env python3
"""D27: read the Phuket FB buyer post via a fresh tab (old one timed out)."""
import sys, time, json
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval
import urllib.request, json as J

# find a healthy tab to drive Target.createTarget from
tabs = [t for t in get_tabs() if t['type']=='page']
host = None
for t in tabs:
    if 'facebook.com' in t.get('url','') and 'groups/271951' not in t.get('url',''):
        host = t; break
if not host:
    host = tabs[0]
print('host tab:', host['url'][:90])
ws = connect(host)
cdp = make_cdp(ws)
url = 'https://www.facebook.com/groups/phuketandthailand/posts/3328765823998690/'
r = cdp('Target.createTarget', {'url': 'about:blank'})
newid = r.get('targetInfo',{}).get('targetId')
print('new tab id:', newid)
time.sleep(2)
cdp('Target.attachToTarget', {'targetId': newid, 'flatten': True})
# use a separate ws for the new target
info = J.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read().decode())
tgt = [x for x in info if x.get('id')==newid]
if not tgt:
    print('new tab not in list'); ws.close(); raise SystemExit
nws = connect(tgt[0])
ncdp = make_cdp(nws)
ncdp('Page.enable')
ncdp('Page.navigate', {'url': url})
time.sleep(12)
v = js_eval(nws, """(() => {
  const t = document.body ? document.body.innerText : '';
  return JSON.stringify(t.replace(/\\s+/g,' ').slice(0,3000));
})()""", await_promise=False)
nws.close()
print('POST TEXT:')
print(str(v)[10:3100])
