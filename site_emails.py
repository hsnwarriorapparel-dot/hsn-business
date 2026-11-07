"""Extract emails from a site, falling back to the real browser.

Many small company sites are JavaScript-rendered, so curl gets the shell but
not the content. This loads the page in the work browser and reads the
rendered text plus any mailto: links.

Run:  python3 site_emails.py <url> [<url> ...]
"""
import json
import re
import sys
import time

sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect

EMAIL_RE = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
BAD_LOCAL = re.compile(
    r'^(no-reply|noreply|donotreply|postmaster|abuse|hostmaster|'
    r'webmaster|post|mail|email|admin|support|help)@', re.I)


def browser_emails(url):
    """Load the url in the browser and pull emails from the rendered page."""
    tabs = get_tabs()
    gm = [t for t in tabs if 'mail.google' in (t.get('url') or '') and t.get('type') == 'page']
    if not gm:
        return [], ''
    ws = connect(gm[0]); _n = [0]

    def cdp(m, p=None, sid=None):
        _n[0] += 1; mid = _n[0]
        msg = {'id': mid, 'method': m, 'params': p or {}}
        if sid: msg['sessionId'] = sid
        ws.send(json.dumps(msg))
        t = time.time() + 50
        while time.time() < t:
            d = json.loads(ws.recv())
            if d.get('id') == mid:
                if 'error' in d:
                    raise RuntimeError(d['error'])
                return d.get('result', {})
        raise TimeoutError(m)

    def ev(e, s):
        r = cdp('Runtime.evaluate', {'expression': e, 'returnByValue': True,
                                     'awaitPromise': True}, sid=s)
        if r.get('exceptionDetails'):
            return ''
        return r.get('result', {}).get('value')

    tid = cdp('Target.createTarget', {'url': url})['targetId']
    s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
    cdp('Page.enable', sid=s)
    time.sleep(8)
    raw = ev("""(()=>{
      const body = document.body ? document.body.innerText : '';
      const mailtos = [...document.querySelectorAll('a[href^="mailto:"]')]
        .map(a => (a.getAttribute('href')||'').replace(/^mailto:/i,'').split('?')[0]);
      const html = document.documentElement ? document.documentElement.innerHTML : '';
      return JSON.stringify({body: body.slice(0, 4000), mailtos, html: html.slice(0, 120000)});
    })()""", s)
    try:
        d = json.loads(raw)
    except Exception:
        d = {'body': '', 'mailtos': [], 'html': ''}
    try:
        cdp('Target.closeTarget', {'targetId': tid})
    except Exception:
        pass
    try:
        ws.close()
    except Exception:
        pass
    found = []
    for e in re.findall(EMAIL_RE, d.get('html', '') + ' ' + d.get('body', '')):
        e = e.lower()
        if e not in found and not BAD_LOCAL.match(e) and 'example' not in e:
            found.append(e)
    return found, d.get('body', '')


if __name__ == '__main__':
    for u in sys.argv[1:]:
        em, body = browser_emails(u)
        print('=== %s' % u)
        print('  emails:', em[:8])
        print('  body  :', body[:200].replace('\n', ' | '))
