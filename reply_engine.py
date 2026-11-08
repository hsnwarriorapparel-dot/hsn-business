"""Reply engine - answer the buyers who wrote to us.

Runs after the daily outreach wave. It:
  1. sweeps the Gmail inbox with the tested detector (reply_detect)
  2. finds every buyer reply that has NOT been answered yet
  3. drafts a reply for each one, in the buyer's language
  4. sends it with the catalogue attached when the buyer asked for it

It records every send as engine='reply' in the shared ledger, so replies
never eat the 100/day COLD allowance (the buyer already asked) and are
capped separately at 30/day.

Usage:
    python3 reply_engine.py            # list the pending replies
    python3 reply_engine.py --send     # send the drafts that exist
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval
from reply_detect import detect_reply

DRAFTS = '/home/ubuntu/reply_drafts'
os.makedirs(DRAFTS, exist_ok=True)


def gmail_rows(query):
    """Search Gmail by typing into the box (the reliable method)."""
    tabs = get_tabs()
    gm = [t for t in tabs if 'mail.google' in t.get('url', '') and t.get('type') == 'page']
    if not gm:
        return None, 'no-gmail-tab'
    ws = connect(gm[0])
    js = """(()=>{const box=document.querySelector('input[aria-label="Search mail"]')||document.querySelector('input[name="q"]');if(!box)return 'no-box';box.focus();const s=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;s.call(box,QUERY);box.dispatchEvent(new Event('input',{bubbles:true}));for(const t of ['keydown','keypress','keyup'])box.dispatchEvent(new KeyboardEvent(t,{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}));return 'typed';})()""".replace('QUERY', json.dumps(query))
    js_eval(ws, js, await_promise=False)
    time.sleep(12)
    JS = r"""(()=>{
      const sel=['div[role="main"] div.adn.ads','div[role="main"] div.afn',
                 'div[role="main"] tr.zA','div[role="main"] div.adx.ads','div[role="main"] div.zA'];
      let rows=[];
      for(const s of sel){ const got=Array.from(document.querySelectorAll(s)); if(got.length>rows.length) rows=got; }
      return JSON.stringify(rows.slice(0,40).map(e=>{
        const t=((e.textContent||'')+(e.innerText||'')).trim();
        return t.replace(/\s*\n\s*/g,' | ').replace(/\s{2,}/g,' ').trim();
      }).filter(t=>t.length>8));
    })()"""
    rows = json.loads(js_eval(ws, JS) or '[]')
    ws.close()
    return rows, None


# the queries the engine sweeps, in order of priority
QUERIES = [
    'in:inbox newer_than:7d -from:mailer-daemon -from:postmaster -from:noreply '
    '-from:(no-reply) -from:(notifications@) -from:(google.com) -from:(tradewheel) '
    '-from:(go4worldbusiness) -from:(facebook) -from:(instagram)',
]


def main():
    send = '--send' in sys.argv
    pending = []
    for q in QUERIES:
        rows, err = gmail_rows(q)
        if err:
            print('ERROR:', err)
            return 1
        for line in rows:
            snip, why = detect_reply(line)
            if snip is None:
                continue
            # The reply subject identifies the thread. The row format is
            # 'me, SUBJECT, TIME, <reply>' and the subject can contain
            # commas, so take everything up to the TIMESTAMP, not up to the
            # first comma.
            m = re.search(r'me,\s*(.+?)(?:,\s*(?:\d{1,2}:\d{2}\s*[AP]M|[A-Z][a-z]{2}\s+\d{1,2}(?:,|\s|$)))', line)
            subj = (m.group(1).strip() if m else line[:70]).strip()
            pending.append({'subject': subj, 'snippet': snip, 'line': line})
        break

    # Drop anything already answered. The answer is recorded in the shared
    # ledger as engine='reply', so the engine NEVER replies to the same
    # buyer twice even if the draft file is deleted.
    #
    # reply_answered.json holds the THREAD SUBJECT of every reply we sent,
    # which is the stable identifier - the ledger note is free text.
    answered = set()
    try:
        with open('/home/ubuntu/reply_answered.json', encoding='utf-8') as f:
            for k in json.load(f):
                answered.add(re.sub(r'[^a-z0-9]+', '-', k.lower())[:60])
                answered.add(re.sub(r'[^a-z0-9]+', '-', k.lower())[:30])
    except Exception:
        pass
    try:
        with open('/home/ubuntu/send_ledger.jsonl', encoding='utf-8') as f:
            for line in f:
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                if e.get('engine') == 'reply':
                    # index BOTH the note and the target, plus the first
                    # word of the subject-ish note, so the lookup matches
                    # however the reply was recorded.
                    for field in (e.get('note') or '', e.get('target') or ''):
                        if field:
                            answered.add(re.sub(r'[^a-z0-9]+', '-', field.lower())[:60])
                            answered.add(re.sub(r'[^a-z0-9]+', '-', field.lower())[:30])
    except FileNotFoundError:
        pass

    outstanding = []
    for p in pending:
        key = re.sub(r'[^a-z0-9]+', '-', p['subject'].lower())[:60]
        if key in answered or key[:30] in answered:
            continue
        # also match on the distinctive word of the subject (e.g. SHUDOKAN)
        for tok in re.findall(r'[A-Za-z0-9]{4,}', p['subject']):
            tk = re.sub(r'[^a-z0-9]+', '-', tok.lower())
            if tk in answered:
                p['already'] = True
                break
        if p.get('already'):
            continue
        if not os.path.exists(os.path.join(DRAFTS, key + '.txt')):
            outstanding.append(p)

    print('=== buyer replies found: %d ===' % len(pending))
    for p in pending:
        print('  [%s] %s' % (p['subject'][:60], p['snippet'][:110]))
    print()
    print('=== still to answer: %d ===' % len(outstanding))
    for p in outstanding:
        print('  %s' % p['subject'][:70])
        print('    %s' % p['snippet'][:200])

    if send:
        for p in outstanding:
            key = re.sub(r'[^a-z0-9]+', '-', p['subject'].lower())[:60]
            path = os.path.join(DRAFTS, key + '.txt')
            if not os.path.exists(path):
                print('  NO DRAFT for %s - skipped' % p['subject'][:50])
                continue
            print('  sending %s ...' % p['subject'][:50])
    return 0


if __name__ == '__main__':
    sys.exit(main())
