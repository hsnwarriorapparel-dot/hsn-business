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
        _s = _j.load(open('/home/ubuntu/day24_quota_state.json'))
        _d = _s.get('date')
        if _d:
            return 'Daily ' + str(_d)
    except Exception:
        pass
    import time as _t
    return 'Daily ' + _t.strftime('%Y-%m-%d', _t.gmtime())
DAY = _day_tag()
LOG = '/home/ubuntu/day24_reply_sweep_log.txt'


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
    import sys as _sys
    _sys.path.insert(0, '/home/ubuntu')
    from leads_safe_write import safe_write_csv
    safe_write_csv(rows, CSV)
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
          // Gmail changed its row DOM on 2026-11-08: the old
          // 'div.adn.ads' selector now returns ZERO rows, so the sweep
          // silently found nothing. The current markup uses 'div.afn'
          // (compact row) and 'tr.zA' (full row). Try every known
          // selector and fall back to a content-based scan, so a future
          // Gmail redesign cannot silently blind the sweep again.
          const sel=['div[role="main"] div.adn.ads','div[role="main"] div.afn',
                     'div[role="main"] tr.zA','div[role="main"] div.adx.ads',
                     'div[role="main"] div.zA'];
          let rows=[];
          for(const s of sel){
            const got=Array.from(document.querySelectorAll(s));
            if(got.length>rows.length) rows=got;
          }
          if(!rows.length){
            // content-based fallback: any element holding a mail row
            const main=document.querySelector('div[role="main"]');
            const re=/[A-Za-z0-9._%+-]+@[^\\s,]+ :: |(^|\\n)me, Mail/;
            const all=Array.from(main.querySelectorAll('div,tr'));
            const cand=all.filter(el=>{
              const t=(el.innerText||'');
              return re.test(t)&&t.length>60&&t.length<1200;
            });
            rows=cand.filter(el=>!cand.some(o=>o!==el&&el.contains(o)));
          }
          // Gmail VIRTUALISES the list: on 2026-11-08 every row's
          // innerText was EMPTY while textContent had the full text.
          // Read textContent first, fall back to innerText.
          rows=rows.slice(0,40).map(e=>{
            const t=((e.textContent||'')+(e.innerText||'')).trim();
            return t.replace(/\\s*\\n\\s*/g,' | ').replace(/\\s{2,}/g,' ').trim();
          }).filter(t=>t.length>8);
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
# A buyer reply does not have to be in English. Shudokan (Spain) asked for
# "catálogo y listado de precios" and the sweep reported 0 human replies
# because every hint word was English.
#
# The sweep also has to ignore OUR OWN outgoing message, which is echoed in
# the thread - otherwise "please send" in our own copy counts as a reply.
from reply_detect import (detect_reply, detect_ig_reply, HUMAN_HINT,  # noqa: E402
                          NOISE_SUBJ)

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
    # reply_detect.detect_reply() is the tested detector - it handles
    # non-English replies, our own quoted message, auto-acks, out-of-office
    # and 'not interested'. 18/18 on the real 2026-11-07 threads.
    human = []
    reasons = {}
    for line in (r.get('rows') or []):
        snip, why = detect_reply(line)
        reasons[why] = reasons.get(why, 0) + 1
        if snip is not None:
            human.append(line)
            log('    HUMAN? | ' + snip[:170])
    log('  rejection reasons: %s' % ', '.join('%s=%d' % (k, v) for k, v in
                                               sorted(reasons.items(), key=lambda x: -x[1])))
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
        ig_reasons = {}
        # Instagram renders the inbox as alternating lines: the contact
        # name, then the message. OUR messages are prefixed "You:" and
        # open with our standard opener - they must never count as a
        # reply. The old check matched any line with an interest word, so
        # 6 of our own outgoing DMs were counted as replies.
        for line in itxt.splitlines():
            line = line.strip()
            if not line:
                continue
            log('    IG| ' + line[:140])
            snip, why = detect_ig_reply(line)
            ig_reasons[why] = ig_reasons.get(why, 0) + 1
            if snip is not None:
                ig_human += 1
                log('    IG HUMAN? | ' + snip[:150])
        log('  IG human-reply candidates: %d' % ig_human)
        log('  IG rejection reasons: %s' % ', '.join(
            '%s=%d' % (k, v) for k, v in sorted(ig_reasons.items(), key=lambda x: -x[1])))
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
log('=== DAY24 REPLY SWEEP DONE ===')
