import sys, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval, make_cdp

igtabs = [t for t in get_tabs() if 'instagram.com' in t.get('url', '') and t.get('type') == 'page']
if not igtabs:
    print('NO IG TAB'); sys.exit(1)
ws = connect(igtabs[0])
cdp = make_cdp(ws)
cdp('Page.enable')
cdp('Page.bringToFront')
time.sleep(2)
txt = js_eval(ws, "(() => (document.body?document.body.innerText:'').slice(0,5000))()", await_promise=False) or ''
ws.close()
print('---- IG INBOX TEXT ----')
print(txt)
