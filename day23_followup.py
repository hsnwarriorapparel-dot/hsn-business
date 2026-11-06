#!/usr/bin/env python3
"""Follow-up email engine for HSN Warrior Apparels.

WHY THIS EXISTS (2026-11-06): 1,950 first-touch emails were sent but only
6 follow-ups. The B2B playbook says buyers need 5-7 touches, and 889 leads
are eligible (emailed 5+ days ago, no reply, no decline, no STOP). This
engine sends ONE business-concrete follow-up to each eligible lead.

GUARDRAILS BUILT IN:
  - Daily quota: hard 100-email ceiling, shared with the first-touch wave
    (both read the SAME dayNN_quota_state.json, so they never exceed 100
    together).
  - Spacing: 40s between sends (Gmail-safe pacing).
  - Exclusion: REPLIED / interested / HOT / declines / STOP / personal
    contacts are never touched.
  - Follow-up spacing: never within 24h of our last outbound to that lead.
  - Copy: passes the spam-word-checker rules (no banned words, no em dash,
    no greeting prefix, no fake urgency, no silence-based stop promise).
  - Row-targeted CSV write: re-reads disk, updates only the dirty row.
  - Resumable: marks each lead 'follow-up sent (Daily <tag>)' immediately
    after a confirmed send, so a re-run never double-sends.

Usage:
  day23_followup.py                 # send up to the remaining quota
  day23_followup.py --limit 5       # foreground test, 5 sends
  day23_followup.py --dry-run       # show what would send, send nothing
"""
import sys, os, time, csv, json, re, argparse, tempfile, random
sys.path.insert(0, '/home/ubuntu')
from outreach import gmail_send
from templates import COMPANY, EMAIL, PHONE

CSV = '/home/ubuntu/leads.csv'
STATE = '/home/ubuntu/day23_quota_state.json'
LOG = '/home/ubuntu/day23_followup_log.txt'
PACE = 40
MIN_AGE_DAYS = 5

ap = argparse.ArgumentParser()
ap.add_argument('--limit', type=int, default=0)
ap.add_argument('--dry-run', action='store_true')
ap.add_argument('--state', default=STATE)
ap.add_argument('--log', default=LOG)
args = ap.parse_args()


def log(m):
    line = time.strftime('%H:%M:%S') + ' ' + m
    print(line, flush=True)
    with open(args.log, 'a') as f:
        f.write(line + '\n')


def newest_state():
    """The newest dayNN_quota_state.json on disk - the day tag must never be
    a hardcoded literal (fix 2026-11-06)."""
    import glob
    states = sorted(glob.glob('/home/ubuntu/day*_quota_state.json'))
    for s in reversed(states):
        try:
            if json.load(open(s)).get('date'):
                return s
        except Exception:
            continue
    return args.state


def day_tag():
    try:
        s = json.load(open(newest_state()))
        d = s.get('date')
        if d:
            return 'Daily ' + str(d)
    except Exception:
        pass
    return 'Daily ' + time.strftime('%Y-%m-%d', time.gmtime())


DAY = day_tag()
DAY_DATE = DAY.replace('Daily ', '')

# --------------------------------------------------------------------------
# ELIGIBILITY
# --------------------------------------------------------------------------
NEVER = re.compile(
    r'replied|reply from|interested|inquiry|inbound|hOT LEAD|hot lead|'
    r'decline|not looking for new supplier|closed account|\bSTOP\b|do not contact|'
    r'no longer interested|unsubscribe', re.I)
PERSONAL = re.compile(r'sayyam|shamas|afzal|chacho|nadeem', re.I)
HAVE_FU = re.compile(r'follow-?up\s*\d?\s*sent|follow-?up sent|follow-?up \(', re.I)
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$')

# Federations, directories and marketplaces are NOT buyers. A gym email that
# happens to sit on a governing-body domain wastes a follow-up touch.
BAD_DOMAINS = (
    'usaboxing.org', 'teamusa', 'yelp.', 'classpass', 'meetup', 'yellowpages',
    'thumbtack', 'tripadvisor', 'ffjudo', 'ffkarate', 'fijlkam', 'judobund',
    'wako', 'britishjudo', 'ffboxe', 'kickboxen-deutschland', 'fkb.nl',
    'olympics.com', 'fisu.net', 'ita-itf.org', 'rita-itf.org', 'ita-official.org',
    'itftkd', 'aiki-federation', 'ifma', 'ifbb', 'wku.', 'ibjjf.com', 'ijf.org',
    'facebook.com', 'instagram.com', 'linkedin.com', 'google.com', 'sentry.io',
    'wixpress.com', 'example.com', 'mydomain', 'yourdomain', 'test.com',
)


def is_bad_email(e):
    low = (e or '').strip().lower()
    if not low:
        return True
    if any(b in low for b in BAD_DOMAINS):
        return True
    # placeholder / constructed addresses
    local, _, dom = low.partition('@')
    if local in ('info', 'sales', 'contact', 'admin', 'noreply', 'no-reply',
                 'mail', 'email', 'hello', 'test', 'example', 'asdf'):
        # generic locals are FINE on a real business domain, but only if the
        # domain itself is a real site - keep them, reject only if domain is
        # junk (handled above). Nothing to do here.
        pass
    if dom in ('example.com', 'domain.com', 'email.com', 'yoursite.com',
               'company.com', 'test.com'):
        return True
    return False


def load_rows():
    with open(CSV, newline='', encoding='utf-8-sig') as f:
        return list(csv.reader(f))


def norm_date(s):
    try:
        return tuple(int(x) for x in s.split('-'))
    except Exception:
        return None


def sent_dates(status):
    return re.findall(r'email sent \(Daily (\d{4}-\d{2}-\d{2})\)', status)


def eligible_leads(rows):
    """First-touch leads sent MIN_AGE_DAYS+ ago, no reply, no decline, no
    prior follow-up, and with a usable email address."""
    hdr = rows[0]
    idx = {h: i for i, h in enumerate(hdr)}
    today = norm_date(DAY_DATE)
    out = []
    for r in rows[1:]:
        if not r or len(r) <= idx['Status']:
            continue
        name = (r[idx['Name']] if idx['Name'] < len(r) else '') or ''
        status = r[idx['Status']] if idx['Status'] < len(r) else ''
        email = (r[idx['Email']] if idx['Email'] < len(r) else '') or ''
        notes = (r[idx['Notes']] if idx['Notes'] < len(r) else '') or ''
        blob = ' '.join((name, status, notes))
        if NEVER.search(blob):
            continue
        if PERSONAL.search(blob):
            continue
        if HAVE_FU.search(status):
            continue
        ds = sent_dates(status)
        if not ds:
            continue
        d = norm_date(ds[-1])
        if not d or not today:
            continue
        # age in days
        import datetime
        age = (datetime.date(*today) - datetime.date(*d)).days
        if age < MIN_AGE_DAYS:
            continue
        e = email.strip()
        if not EMAIL_RE.match(e):
            continue
        if is_bad_email(e):
            continue
        out.append({
            'id': r[idx['Lead ID']],
            'name': name.strip() or 'your team',
            'email': e,
            'country': (r[idx['Country']] if idx['Country'] < len(r) else '') or '',
            'age': age,
            'status': status,
        })
    # oldest first: the ones with the most silence get first touch again
    out.sort(key=lambda x: (-x['age'], x['id']))
    return out


# --------------------------------------------------------------------------
# COPY (spam-word-checker compliant)
# --------------------------------------------------------------------------
SUBJECTS = [
    "Re: Custom martial arts gear for {name}",
    "{company} - quick question on {name}",
    "Re: {name} x {company} - custom club apparel",
]

# Three rotating follow-up angles. Each is business-concrete: a specific
# product, a specific price anchor, and a next step that serves THEIR club.
# No 'just following up', no urgency, no silence-based stop promise.
ANGLES = [
    {
        'key': 'price',
        'body': """{name} team,

Our pricing for club quantities:

- Jiu-Jitsu Gi (450g): EUR 29.60
- Rash Guard: EUR 9.50
- MMA Shorts: EUR 9.90
- Jiu-Jitsu Belt: EUR 3
- Boxing Gloves (cowhide): EUR 25.50

Every order includes your club's own logo, and we handle shipping and customs
so the total that lands at your door has no added fees.

How many pieces of each would your club need for a first run?

Best regards,
{company}
{email}
{phone}""",
    },
    {
        'key': 'moq',
        'body': """{name} team,

One thing we hear from clubs like yours: large manufacturers push 100-piece
minimums, and that is too much to try on a first order.

Our minimum is 10 pieces per item. That lets a club start with a few pieces
per size, check the fit and the stitching on real people, then order for the
whole group once it works.

We can build a mockup with your logo and colours before anything goes into
production. Which items would you want to see first?

Best regards,
{company}
{email}
{phone}""",
    },
    {
        'key': 'leadtime',
        'body': """{name} team,

Production takes 3-4 weeks from artwork approval, then 4-6 working days by
courier (DHL, FedEx or UPS, door to door).

That matters if your club has a term start, a competition season or an
opening date to hit. If you tell us the date the gear needs to be in your
hands, we work backwards from it and tell you what is realistic.

What is the date you would want the gear to arrive?

Best regards,
{company}
{email}
{phone}""",
    },
]


def region_phrase(country):
    c = (country or '').strip().lower()
    usa = ('usa', 'united states', 'us', 'america')
    if any(c == x or c.startswith(x) for x in usa):
        return 'across the United States'
    return 'across Europe'


def build_followup(lead, angle):
    subject = random.choice(SUBJECTS).format(name=lead['name'], company=COMPANY)
    body = angle['body'].format(name=lead['name'], company=COMPANY,
                                email=EMAIL, phone=PHONE)
    return subject, body


# --------------------------------------------------------------------------
# STATUS WRITE (row-targeted, atomic)
# --------------------------------------------------------------------------
def update_status(lead_id, new_status):
    rows = load_rows()
    idx = {h: i for i, h in enumerate(rows[0])}
    for r in rows[1:]:
        if r and r[0] == lead_id:
            cur = (r[idx['Status']] if idx['Status'] < len(r) else '') or ''
            r[idx['Status']] = (cur.rstrip(' |') + ' | ' + new_status)[:250]
            break
    fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
    with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows(rows)
    os.replace(tmp, CSV)


def sent_today_count():
    """Count emails marked sent TODAY by any sender (first-touch + follow-up).
    A row counts only when the SAME marker carries the action and the day."""
    rows = load_rows()
    hdr = rows[0]
    idx = {h: i for i, h in enumerate(hdr)}
    n = 0
    for r in rows[1:]:
        if len(r) <= idx['Status']:
            continue
        st = r[idx['Status']] or ''
        for part in st.split('|'):
            low = part.lower()
            if ('email sent' in low or 'follow-up sent' in low) and DAY_DATE in part:
                n += 1
                break
    return n


def quota_remaining():
    try:
        s = json.load(open(newest_state()))
        daily = int(s.get('daily_email_quota', 100))
    except Exception:
        daily = 100
    return max(0, daily - sent_today_count())


def main():
    log(f'=== FOLLOW-UP ENGINE START ({DAY}) ===')
    rows = load_rows()
    leads = eligible_leads(rows)
    remaining = quota_remaining()
    log(f'  eligible leads   : {len(leads)}')
    log(f'  quota remaining  : {remaining}')
    if not leads:
        log('  nothing to follow up')
        return
    if remaining <= 0:
        log('  DAILY EMAIL QUOTA ALREADY REACHED - nothing sent')
        return

    limit = args.limit or remaining
    limit = min(limit, remaining)
    log(f'  will send        : {limit}')

    if args.dry_run:
        for lead in leads[:limit]:
            print(f"  {lead['id']} | {lead['age']}d | {lead['name'][:28]:<28} | {lead['email'][:34]} | {lead['country'][:18]}")
        return

    sent = 0
    failed = 0
    for i, lead in enumerate(leads[:limit], 1):
        # RE-CHECK THE QUOTA BEFORE EVERY SEND (fix 2026-11-06): the limit was
        # computed once at startup, so a concurrent first-touch wave could
        # send its quota while this engine was running and both together would
        # overshoot 100. Read the live CSV each time.
        if quota_remaining() <= 0:
            log(f'  QUOTA REACHED at {lead["id"]} - stopping, remaining stay queued')
            break
        angle = ANGLES[(i - 1) % len(ANGLES)]
        subject, body = build_followup(lead, angle)
        log(f"  [{i}/{limit}] FOLLOW-UP {lead['id']} {lead['name'][:26]} -> {lead['email']} ({angle['key']})")
        try:
            res = gmail_send(lead['email'], subject, body)
        except Exception as e:
            res = 'exception: %s' % e
        if res == 'sent':
            sent += 1
            update_status(lead['id'], 'follow-up sent (%s, %s)' % (DAY, angle['key']))
            log(f'      OK')
        else:
            failed += 1
            log(f'      FAILED: {res}')
            if 'no-gmail-tab' in str(res):
                log('      GMAIL TAB GONE - stopping, remaining stay queued')
                break
        if i < limit:
            time.sleep(PACE)
    log(f'=== FOLLOW-UP ENGINE DONE: {sent} sent, {failed} failed ===')


if __name__ == '__main__':
    main()
