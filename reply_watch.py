#!/usr/bin/env python3
"""Sprint reply watch: hourly sweep of Gmail replies + IG DMs; logs + drafts new replies."""
import sys, time, json, os
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval, find_tab

LOG = '/home/ubuntu/reply_watch_log.txt'
DRAFTS = '/home/ubuntu/drafts'
os.makedirs(DRAFTS, exist_ok=True)
STATE = '/home/ubuntu/reply_watch_state.json'

def log(m):
    line = time.strftime('%Y-%m-%d %H:%M:%S') + ' ' + m
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')

def load_state():
    try:
        return json.load(open(STATE))
    except Exception:
        return {'gmail_seen': [], 'ig_seen': []}

def save_state(s):
    json.dump(s, open(STATE, 'w'))

def check_gmail(state):
    """Check for NEW human replies (exclude bounces, sent mail, auto-acks)."""
    tabs = get_tabs()
    gm = [t for t in tabs if 'mail.google' in t.get('url','') and t['type'] == 'page']
    if not gm:
        log('gmail tab missing - skip this tick')
        return
    ws = connect(gm[0])
    cdp = make_cdp(ws)
    cdp("Page.navigate", {"url": "https://mail.google.com/mail/u/0/#search/-from%3Ame+bq_%3D%22f%3Ahsnwarriorapparel%22+newer_than%3A1d"})
    time.sleep(12)
    v = js_eval(ws, '''(() => {
      const rows = Array.from(document.querySelectorAll('tr')).slice(0, 15);
      return JSON.stringify(rows.map(r => (r.innerText || '').split('\\n').slice(0, 3).join(' | ').slice(0, 120)).filter(t => t.length > 12));
    })()''')
    try:
        items = json.loads(v)
    except Exception:
        items = []
    new = []
    for it in items:
        low = it.lower()
        if any(x in low for x in ['mailer-daemon', 'delivery', 'blocked', 'noreply', 'no-reply', 'support@', 'news@']):
            continue
        key = it[:60]
        if key not in state['gmail_seen']:
            state['gmail_seen'].append(key)
            new.append(it)
    if new:
        for n in new:
            log('NEW GMAIL REPLY: ' + n[:100])
            fn = f"{DRAFTS}/gmail_reply_{int(time.time())}.txt"
            with open(fn, 'w') as f:
                f.write(n)
    else:
        log('gmail: no new human replies')
    ws.close()

def check_ig(state):
    """Check IG DM inbox for new messages."""
    tabs = get_tabs()
    igt = [t for t in tabs if 'instagram' in t.get('url','') and t['type'] == 'page']
    if not igt:
        log('ig tab missing - skip')
        return
    ws = connect(igt[0])
    cdp = make_cdp(ws)
    cdp("Page.navigate", {"url": "https://www.instagram.com/direct/inbox/"})
    time.sleep(12)
    v = js_eval(ws, '''(() => {
      const t = document.body ? document.body.innerText : '';
      const requests = t.includes('Requests');
      const unread = [...document.querySelectorAll('[aria-label*="unread"], .x1i10v2x[aria-label]')].length;
      return JSON.stringify({head: t.replace(/\\n/g, ' ').slice(0, 200), hasRequests: requests});
    })()''')
    try:
        d = json.loads(v)
    except Exception:
        d = {}
    if d.get('hasRequests'):
        log('IG DM REQUESTS PRESENT: ' + d.get('head', '')[:100])
    else:
        log('ig: inbox checked, no requests flag')
    ws.close()

def main():
    log('=== REPLY WATCH TICK ===')
    state = load_state()
    try:
        check_gmail(state)
    except Exception as e:
        log(f'gmail check error: {str(e)[:50]}')
    try:
        check_ig(state)
    except Exception as e:
        log(f'ig check error: {str(e)[:50]}')
    # WA skipped while logged out; re-enable after QR scan
    save_state(state)
    log('tick complete')

if __name__ == '__main__':
    main()
