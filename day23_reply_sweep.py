#!/usr/bin/env python3
"""Day-22 (2026-11-05) reply sweep + final verification.

FIX (2026-11-05): the old sweep navigated by hash-URL, which SILENTLY fails
- the query never applies and the page keeps showing the previous list, so
the sweep reported "0 replies" while never having searched. The skill's
pipeline-timing.md says the same: "A hash-URL sweep reporting '0 replies'
means nothing; always confirm with the typing method".

This version TYPES the query into the real 'Search mail' input and reads the
rendered result, so a query that does not apply is visible as a stale list.
"""
import csv, os, re, sys, json, time, tempfile
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval, make_cdp

CSV = '/home/ubuntu/leads.csv'
def _day_tag():
    """The day tag MUST come from the quota-state file, never a hardcoded
    literal (fix 2026-11-06): a copied literal kept yesterday's date, so the
    runner counted yesterday's sends as 'already sent today' and refused to
    send anything on a fresh day."""
    try:
        import json as _j
        _s = _j.load(open('/home/ubuntu/day23_quota_state.json'))
        _d = _s.get('date')
        if _d:
            return 'Daily ' + str(_d)
    except Exception:
        pass
    import time as _t
    return 'Daily ' + _t.strftime('%Y-%m-%d', _t.gmtime())
DAY = _day_tag()
LOG = '/home/ubuntu/day23_reply_sweep_log.txt'


def log(m):
    line = time.strftime('%H:%M:%S') + ' ' + m
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')


def update_status(lead_id, new_status):
    rows = list(csv.reader(open(CSV, newline='', encoding='utf-8-sig')))
    idx = {h: i for i, h in enumerate(rows[0])}
    hit = False
    for r in rows[1:]:
        if r and r[0] == lead_id:
            r[idx['Status']] = (r[idx['Status']].rstrip(' |') + ' | ' + new_status)[:250]
            hit = True
    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(rows)
    os.replace(tmp, CSV)
    return hit


# ---------- Gmail search that actually applies ----------
class GmailSearch:
    def __init__(self):
        tabs = get_tabs()
        gm = [t for t in tabs if 'mail.google' in t.get('url', '') and t.get('type') == 'page']
        if not gm:
            raise RuntimeError('NO GMAIL TAB')
        self.ws = connect(gm[0])
        self.cdp = make_cdp(self.ws)
        self.cdp('Page.enable')
        self.cdp('Page.bringToFront')
        time.sleep(2)

    def search(self, query, wait=8):
        """Type the query into the real Search-mail input, press Enter, read
        the rendered list. Returns the list text + the conversation count."""
        js = """(()=>{
          const box=document.querySelector('input[aria-label="Search mail"]') ||
                    document.querySelector('input[name="q"]');
          if(!box) return 'no-box';
          box.focus();
          const setter=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
          setter.call(box,%s);
          box.dispatchEvent(new Event('input',{bubbles:true}));
          for (const type of ['keydown','keypress','keyup']) {
            box.dispatchEvent(new KeyboardEvent(type,{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}));
          }
          return 'typed';
        })()""" % json.dumps(query)
        r = js_eval(self.ws, js, await_promise=False)
        if r == 'no-box':
            raise RuntimeError('search box not found')
        time.sleep(wait)
        v = js_eval(self.ws, """(()=>{
          const m=document.querySelector('div[role="main"]');
          const t=m?m.innerText:'';
          const box=document.querySelector('input[aria-label="Search mail"]');
          const mm=t.match(/([\\d,]+)\\s*[–-]\\s*[\\d,]+\\s+of\\s+([\\d,]+)/);
          const nomatch=/No messages matched/i.test(t);
          const many=/of many/i.test(t);
          const rows=Array.from(document.querySelectorAll('div[role="main"] div.adn.ads'))
                    .slice(0,40).map(e=>(e.innerText||'').replace(/\\n/g,' | '));
          return JSON.stringify({count:mm?mm[2]:null,nomatch:nomatch,many:many,
                                  box:box?box.value:'',rows:rows,head:t.slice(0,200)});
        })()""", await_promise=False)
        try:
            return json.loads(v or '{}')
        except Exception:
            return {'raw': str(v)[:300]}

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


# Bounce / auto-ack / platform noise must not be reported as client replies.
NOISE_SUBJ = re.compile(
    r'delivery incomplete|address not found|message not delivered|message blocked|'
    r'undeliverable|mail delivery failed|returned mail|auto.?reply|automatic reply|'
    r'out of office|we are away|read receipt|unsubscribe|tracking|receipt|'
    r'password|verify your|welcome to|newsletter|promotion|offer|'
    r'tradewheel|go4worldbusiness|facebook|instagram|amazon|etsy|meta|'
    r'western union|yahoo|etsy|aliexpress|alibaba', re.I)
HUMAN_HINT = re.compile(
    r'we (are|would) (like|be interested)|interested in|quotation|quote|price list|'
    r'catalog|how much|minimum order|moq|sample|interested|please send|'
    r'could you send|can you send|can you share|would like to know', re.I)


# ---------- 1. Gmail reply sweep ----------
log('--- Gmail reply sweep (7d inbox, TYPING method) ---')
try:
    gs = GmailSearch()
    # The inbox query is built to exclude the usual noise senders, but the
    # -from: filter does NOT remove bounce threads (Gmail lists OUR OWN
    # address in the "from" span of the "me, Mail" version of each bounce),
    # so the SUBJECT is filtered separately below.
    q_inbox = ('in:inbox newer_than:7d -from:mailer-daemon -from:postmaster '
               '-from:noreply -from:(no-reply) -from:(notifications@) '
               '-from:(google.com) -from:(tradewheel) -from:(go4worldbusiness) '
               '-from:(facebook) -from:(instagram)')
    r = gs.search(q_inbox, wait=10)
    log('  query applied: %r' % (r.get('box') or ''))
    log('  conversations: %s (many=%s nomatch=%s)' % (r.get('count'), r.get('many'), r.get('nomatch')))
    human = []
    for line in (r.get('rows') or []):
        if NOISE_SUBJ.search(line):
            continue
        if HUMAN_HINT.search(line):
            human.append(line)
            log('    HUMAN? | ' + line[:170])
    log('  HUMAN client-reply candidates: %d' % len(human))
    if not human:
        for line in (r.get('rows') or [])[:12]:
            log('    | ' + line[:160])

    # STOP / opt-out keyword scan over a wider window
    r2 = gs.search('in:inbox newer_than:30d', wait=10)
    log('  --- STOP / opt-out scan (30d) ---')
    stops = 0
    for line in (r2.get('rows') or []):
        for kw in ('STOP', 'unsubscribe', 'remove me', 'do not contact', 'no thanks'):
            if kw.lower() in line.lower():
                log('  KEYWORD %r: %s' % (kw, line[:170]))
                stops += 1
                break
    log('  STOP/opt-out hits: %d' % stops)

    # bounces in the last 2 days (subject-filtered, not from:-filtered)
    r3 = gs.search('in:inbox newer_than:2d ("Delivery incomplete" OR '
                   '"Address not found" OR "Message not delivered" OR '
                   '"Message blocked" OR "Undelivered Mail")', wait=10)
    log('  --- bounces (2d) ---')
    log('  bounce conversations: %s (many=%s nomatch=%s)'
        % (r3.get('count'), r3.get('many'), r3.get('nomatch')))
    for line in (r3.get('rows') or [])[:25]:
        log('    B| ' + line[:150])
    gs.close()
except Exception as e:
    log('  Gmail sweep error: ' + str(e)[:200])

# ---------- 2. IG inbox sweep for replies ----------
log('--- IG inbox reply sweep ---')
try:
    igtabs = [t for t in get_tabs() if 'instagram.com' in t.get('url', '')
              and t.get('type') == 'page']
    if not igtabs:
        log('  no IG tab')
    else:
        ws = connect(igtabs[0])
        cdp = make_cdp(ws)
        cdp('Page.bringToFront')
        cdp('Page.navigate', {'url': 'https://www.instagram.com/direct/inbox/'})
        time.sleep(12)
        itxt = js_eval(ws, """(() => (document.body?document.body.innerText:'').slice(0,4000))()""",
                       await_promise=False) or ''
        ig_human = 0
        for line in itxt.splitlines():
            if line.strip():
                log('    IG| ' + line.strip()[:140])
                if HUMAN_HINT.search(line) and not NOISE_SUBJ.search(line):
                    ig_human += 1
        log('  IG human-reply candidates: %d' % ig_human)
        ws.close()
except Exception as e:
    log('  IG sweep error: ' + str(e)[:200])

# ---------- 3. canonical counters ----------
log('--- final counters ---')
try:
    import io, contextlib, runpy
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        runpy.run_path('/home/ubuntu/hsn_counters.py', run_name='__main__')
    for line in buf.getvalue().splitlines():
        log('  ' + line)
except Exception as e:
    log('  hsn_counters error: ' + str(e)[:200])
log('=== DAY23 REPLY SWEEP DONE ===')
