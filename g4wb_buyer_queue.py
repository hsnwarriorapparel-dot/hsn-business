#!/usr/bin/env python3
"""go4WorldBusiness daily buyer-inquiry queue.

WHY (2026-11-07): the JUNIOR membership allows only ONE buyer inquiry per day
(max 2 per week). The first one we sent was a 400-piece karate belt order. But
the feed holds far bigger martial-arts RFQs - 3,500 taekwondo belts for
Malaysia, 500-1,000 boxing accessories for Egypt - and every time we let the
daily slot go unused, a real order goes to a competitor instead.

THE TWO RULES THAT DECIDE WHAT CAN BE SENT
  1. A buylead can only be inquired about 5 DAYS after it was posted.
  2. JUNIOR = 1 buyer inquiry per day free. Premium = 100/day.

THE PLAN: this script keeps a ranked queue of eligible RFQs. Each day it
sends the highest-value one, writes the result, and moves on. The captcha is
regenerated on every page load, so the send is TWO PHASE (see
g4wb_inquiry_send.py) - this script drives both phases in one go by reading
the captcha image with the same vision model.

RUN:  python3 g4wb_buyer_queue.py            # send today's one inquiry
      python3 g4wb_buyer_queue.py --list     # show the ranked queue
      python3 g4wb_buyer_queue.py --add <url-slug> <qty> <buyer> <date>
"""
import csv
import datetime
import glob
import json
import os
import re
import subprocess
import sys
import time

QUEUE = '/home/ubuntu/g4wb_buyer_queue.json'
STATE = '/home/ubuntu/g4wb_buyer_queue_state.json'
TARGETS = '/home/ubuntu/g4wb_top_targets.json'
PY = subprocess.run(['bash', '-lc',
                     'ls -d /home/ubuntu/.hermes/tools/python-3*/bin/python3 2>/dev/null | sort -V | tail -1'],
                    capture_output=True, text=True).stdout.strip()

sys.path.insert(0, '/home/ubuntu')


def load_queue():
    try:
        return json.load(open(QUEUE))
    except Exception:
        return []


def load_state():
    try:
        return json.load(open(STATE))
    except Exception:
        return {}


def save_state(s):
    json.dump(s, open(STATE, 'w'), indent=2, ensure_ascii=False)


def sent_today_on_platform():
    """How many buyer inquiries already went out today. The sent-list page is
    the ground truth; the local log is the fallback."""
    st = load_state()
    d = st.get('last_sent_date')
    n = st.get('sent_today_count', 0)
    if d == today_str():
        return n
    return 0


def today_str():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')


def age_days(datestr):
    if not datestr:
        return 0
    try:
        dt = datetime.datetime.strptime(datestr, '%b-%d-%y').date()
    except Exception:
        return 0
    return (datetime.datetime.now(datetime.timezone.utc).date() - dt).days


def qty_num(q):
    q = (q or '').replace(',', '')
    m = re.search(r'([\d.]+)\s*(Pieces|pcs|Unit/Units|Units)', q, re.I)
    if not m:
        return 0
    try:
        return int(float(m.group(1)))
    except Exception:
        return 0


def eligible(item):
    """5-day rule + not premium-only + not already sent."""
    if item.get('sent'):
        return False, 'already sent'
    if item.get('premium'):
        return False, 'premium only'
    if age_days(item.get('date')) < 5:
        return False, 'posted %dd ago (needs 5d)' % age_days(item.get('date'))
    return True, 'ok'


def build_queue():
    """Seed the queue from the targets we have already mapped."""
    if load_queue():
        return load_queue()
    q = []
    try:
        tg = json.load(open(TARGETS))
    except Exception:
        tg = {}
    for slug, v in tg.items():
        if not isinstance(v, dict) or 'href' not in v:
            continue
        q.append({
            'slug': slug,
            'href': v['href'],
            'qty': v.get('qty', ''),
            'buyer': (v.get('buyer') or '').replace('Buyer From', '').strip(),
            'date': v.get('date', ''),
            'status': v.get('status', ''),
            'premium': bool(v.get('prem')),
            'sent': False,
            'score': qty_num(v.get('qty', '')),
        })
    json.dump(q, open(QUEUE, 'w'), indent=2, ensure_ascii=False)
    return q


def rank(q):
    """Biggest order first, then oldest-posted first (more likely to still be
    live), then VERIFIED over ARCHIVED."""
    def key(i):
        verified = 0 if i.get('status', '').strip() == 'VERIFIED' else 1
        return (-i.get('score', 0), verified, -age_days(i.get('date')))
    return sorted(q, key=key)


def main():
    args = sys.argv[1:]
    q = build_queue()

    if '--mark' in args:
        i = args.index('--mark')
        mark_sent(args[i + 1], args[i + 2] if len(args) > i + 2 else 'FAILED')
        return

    if '--add' in args:
        i = args.index('--add')
        slug = args[i + 1]
        href = args[i + 2] if len(args) > i + 2 else ''
        qty = args[i + 3] if len(args) > i + 3 else ''
        buyer = args[i + 4] if len(args) > i + 4 else ''
        date = args[i + 5] if len(args) > i + 5 else ''
        q.append({'slug': slug, 'href': href, 'qty': qty, 'buyer': buyer,
                  'date': date, 'status': '', 'premium': False, 'sent': False,
                  'score': qty_num(qty)})
        json.dump(q, open(QUEUE, 'w'), indent=2, ensure_ascii=False)
        print('added %s (%s) to the queue' % (slug, qty))
        return

    r = rank(q)
    if '--list' in args:
        print('=== go4WorldBusiness buyer inquiry queue (1/day, JUNIOR) ===')
        for i, it in enumerate(r, 1):
            ok, why = eligible(it)
            print('%2d. [%s] %-42s qty=%-16s %-16s %s  %s' % (
                i, 'OK ' if ok else 'NO ', it['slug'][:41], (it.get('qty') or '')[:15],
                (it.get('buyer') or '')[:15], it.get('date') or '', '' if ok else '(' + why + ')'))
        print()
        print('sent today so far: %d/1' % sent_today_on_platform())
        return

    # SEND the top eligible one.
    # The captcha is regenerated on every page load, so the send is TWO PHASE:
    #   --prepare  opens the tab and captures the captcha image
    #   --captcha  reattaches to that SAME tab, fills and submits
    # The agent drives both steps because it owns the vision tool that reads
    # the captcha image.
    already = sent_today_on_platform()
    if already >= 1:
        print('DAILY LIMIT REACHED (%d/1 buyer inquiry today) - the queue keeps its place, tomorrow it sends the next one.' % already)
        return

    target = None
    for it in r:
        ok, why = eligible(it)
        if ok:
            target = it
            break
    if not target:
        print('No eligible RFQ in the queue right now.')
        for it in r[:6]:
            ok, why = eligible(it)
            if not ok:
                print('   %-42s %s' % (it['slug'][:41], why))
        return

    print('TARGET=%s' % target['slug'])
    print('HREF=%s' % target['href'])
    print('QTY=%s' % target.get('qty'))
    print('BUYER=%s' % target.get('buyer'))
    print('DATE=%s' % target.get('date'))

    msgfile = ''
    try:
        from g4wb_belt_messages import MESSAGES
        m = MESSAGES.get(target['slug'])
        if m:
            msgfile = '/home/ubuntu/g4wb_queue_msg.txt'
            open(msgfile, 'w', encoding='utf-8').write(m['body'])
            print('MESSAGE_FILE=%s' % msgfile)
    except Exception as e:
        print('MESSAGE_FILE= (no tailored copy: %s)' % e)

    # PHASE 1 - open the inquiry tab and capture its captcha image. The
    # captcha is regenerated on every page load, so phase 2 must reattach to
    # THIS tab (g4wb_inquiry_send.py saves the targetId for that).
    print('PHASE1_RUNNING')
    try:
        if os.path.exists('/home/ubuntu/g4wb_inquiry_target.json'):
            os.unlink('/home/ubuntu/g4wb_inquiry_target.json')
        r1 = subprocess.run([PY, '/home/ubuntu/g4wb_inquiry_send.py', target['href']],
                            capture_output=True, text=True, timeout=300)
        if 'PHASE 1 DONE' in r1.stdout:
            print('PHASE1_OK')
        else:
            print('PHASE1_FAILED')
            print(r1.stdout[-300:])
            print(r1.stderr[-400:])
    except Exception as e:
        print('PHASE1_FAILED %s' % e)


def mark_sent(slug, result):
    """Record the outcome of today's inquiry."""
    q = load_queue()
    for it in q:
        if it.get('slug') == slug:
            if result == 'SENT':
                it['sent'] = True
                it['sent_date'] = today_str()
            break
    json.dump(q, open(QUEUE, 'w'), indent=2, ensure_ascii=False)
    st = load_state()
    st['last_sent_date'] = today_str()
    st['sent_today_count'] = sent_today_on_platform() + (1 if result == 'SENT' else 0)
    st['last_slug'] = slug
    st['last_result'] = result
    st['last_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save_state(st)
    print('marked %s -> %s' % (slug, result))


if __name__ == '__main__':
    main()
