import csv, json, re, sys
from datetime import datetime
import os

sys.path.insert(0, '/home/ubuntu')
from gmaps_daily_scrape import clean_email

with open('/home/ubuntu/gmaps-output/leads_day1_full_clean.json', 'r') as f:
    leads = json.load(f)

# JUNK-FILTER FIX (2026-11-02): the raw scrape cells are COMMA-SEPARATED and
# mix a real address with telemetry noise (sentry.wixpress.com, sentry.io,
# example.com, 32-hex image hashes). This script used to split every cell on
# commas and write ONE TRACKER ROW PER ADDRESS, so the 09:00 automation cron
# emailed ~46 junk telemetry addresses on 2026-11-02 (47 of 50 sends were
# noise; 2 were duplicate re-sends of leads already emailed on 2026-10-29).
# Fix: run every cell through the SAME clean_email() the live scrape uses
# (it rejects sentry/wixpress/placeholder/hash/3rd-party domains and scores
# the rest against the lead's own website + name), so only ONE real address
# per lead ever reaches the tracker.
JUNK_DOMAIN_HINTS = ('sentry', 'wixpress', 'example.com', 'domain.com',
                      'dominio.com', 'mysite.com', 'abuse@', 'postmaster@')


def _clean_cell(l):
    """Return the single usable address for a lead ('' when none is)."""
    cell = (l.get('email') or '').strip()
    if not cell:
        return ''
    site = (l.get('website') or '').strip()
    name = (l.get('title') or '').strip()
    picked = clean_email(cell, site, name)
    if picked:
        return picked
    # clean_email() is strict (needs a site/name signal). Fall back to a
    # single address that is itself clean, so we never lose a valid lead.
    for c in cell.split(','):
        c = c.strip().lower()
        if not c or not re.match(r'^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$', c):
            continue
        if any(h in c for h in JUNK_DOMAIN_HINTS):
            continue
        if re.fullmatch(r'[0-9a-f]{16,}', c.split('@')[0]):
            continue
        if re.search(r'\.(jpg|jpeg|png|gif|webp|svg|pdf|html?)$', c):
            continue
        return c
    return ''


for l in leads:
    l['email'] = _clean_cell(l)

# Never re-send an address that leads.csv already records as emailed.
LEADS_CSV = '/home/ubuntu/leads.csv'
already_sent = set()
if os.path.exists(LEADS_CSV):
    with open(LEADS_CSV, newline='', encoding='utf-8-sig', errors='replace') as f:
        for row in csv.DictReader(f):
            em = (row.get('Email') or '').strip().lower()
            st = (row.get('Status') or '').lower()
            if em and ('email sent' in st or 'failed' in st):
                already_sent.add(em)
if already_sent:
    kept = 0
    for l in leads:
        if (l.get('email') or '').strip().lower() in already_sent:
            l['email'] = ''
        else:
            kept += 1
    print(f'tracker: dropped {len(leads)-kept} lead(s) whose email was already sent/failed in leads.csv')

TRACKER = '/home/ubuntu/gmaps-output/outreach_tracker.csv'

# PRESERVE existing send markers. This script rewrites the tracker from scratch,
# which used to wipe every 'SENT'/'PENDING' marker and make the next automation
# run re-send emails that had already gone out (11 duplicate sends on 2026-10-31).
# Load the old tracker first and carry the per-email status forward.
old_status = {}
if os.path.exists(TRACKER):
    with open(TRACKER, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            em = (row.get('Email') or '').strip().lower()
            if not em:
                continue
            cur = {
                'Email Sent': row.get('Email Sent', '') or '',
                'Email Date': row.get('Email Date', '') or '',
                'IG DM Sent': row.get('IG DM Sent', '') or '',
                'IG DM Date': row.get('IG DM Date', '') or '',
                'WA Sent': row.get('WA Sent', '') or '',
                'WA Date': row.get('WA Date', '') or '',
                'Reply Received': row.get('Reply Received', '') or '',
                'Reply Date': row.get('Reply Date', '') or '',
            }
            prev = old_status.get(em)
            if prev is None:
                old_status[em] = cur
                continue
            # An address can appear on several tracker rows (same gym, different
            # phone/site). A SENT marker on ANY row wins, otherwise the last row
            # would silently downgrade an already-sent address back to READY.
            for k in cur:
                if cur[k] and cur[k] not in ('READY_TO_SEND', 'PENDING', 'NO', 'NEW', ''):
                    prev[k] = cur[k]
                elif not prev.get(k):
                    prev[k] = cur[k]

# Create outreach-ready CSV
with open('/home/ubuntu/gmaps-output/leads_outreach_ready.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['email', 'title', 'category', 'phone', 'website', 'address', 'city', 'state', 'country'])
    for l in leads:
        writer.writerow([l['email'], l['title'], l['category'], l['phone'], l['website'], l['address'], l['city'], l['state'], l['country']])

# Create outreach tracker
with open('/home/ubuntu/gmaps-output/outreach_tracker.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([
        'Date', 'Lead Source', 'Club Name', 'Contact Person', 'Email', 'Phone', 
        'Website', 'City', 'State', 'Country', 'Sport', 'Email Sent', 'Email Date',
        'IG DM Sent', 'IG DM Date', 'WA Sent', 'WA Date', 'Reply Received', 
        'Reply Date', 'Status', 'Notes'
    ])
    for l in leads:
        for email in l['email'].split(','):
            email = email.strip()
            if not email:
                continue
            title_lower = l['title'].lower()
            sport = 'wrestling' if 'wrestling' in title_lower else \
                    'boxing' if 'boxing' in title_lower else \
                    'BJJ' if any(x in title_lower for x in ['bjj', 'jiu jitsu', 'jiu-jitsu']) else \
                    'Muay Thai' if 'muay thai' in title_lower else \
                    'martial arts' if any(x in title_lower for x in ['martial arts', 'karate', 'taekwondo', 'kung fu']) else \
                    'combat sports'
            # carry forward any prior send marker for this address
            prev = old_status.get(email.strip().lower(), {})
            es = prev.get('Email Sent') or 'READY_TO_SEND'
            ed = prev.get('Email Date') or ''
            igs = prev.get('IG DM Sent') or 'PENDING'
            igd = prev.get('IG DM Date') or ''
            was = prev.get('WA Sent') or 'NO'
            wad = prev.get('WA Date') or ''
            rr = prev.get('Reply Received') or 'NO'
            rd = prev.get('Reply Date') or ''
            st = 'SENT' if es == 'SENT' else 'NEW'
            writer.writerow([
                datetime.now().strftime('%Y-%m-%d'),
                'Google Maps Scraper',
                l['title'],
                '',
                email.strip(),
                l['phone'],
                l['website'],
                l['city'],
                l['state'],
                l['country'],
                sport,
                es,
                ed,
                igs,
                igd,
                was,
                wad,
                rr,
                rd,
                st,
                'Day 1 scrape - 137 clean leads'
            ])

# Create email drafts
os.makedirs('/home/ubuntu/gmaps-output/drafts', exist_ok=True)
for l in leads:
    title = l['title']
    email = l['email'].split(',')[0].strip()
    if not email:
        continue
    sport = 'wrestling' if 'wrestling' in title.lower() else \
            'boxing' if 'boxing' in l['title'].lower() else \
            'BJJ' if any(x in l['title'].lower() for x in ['bjj', 'jiu jitsu', 'jiu-jitsu']) else \
            'Muay Thai' if 'muay thai' in l['title'].lower() else \
            'martial arts' if any(x in l['title'].lower() for x in ['martial arts', 'karate', 'taekwondo', 'kung fu']) else \
            'combat sports'
    
    body = f'''Hi {l['title'].split()[0] if l['title'] else 'Team'},

Saw your club online -- impressive program. We're HSN Warrior Apparels, a custom fightwear manufacturer (since 2011).

We make custom gear with your logo, colors, and specs -- direct from our factory at club pricing (10-piece minimum).

Same-day quote with mockup. Just reply with your logo/colors & quantities.

-- HSN Warrior Apparels
+92 337 3336381 | hsnwarriorapparels@gmail.com
https://hsnwarriorapparels.vercel.app'''

    filename = f'/home/ubuntu/gmaps-output/drafts/{l["title"][:50].replace("/", "_")}.eml'
    with open(filename, 'w') as f:
        f.write(f'To: {l["email"].split(",")[0].strip()}\n')
        f.write(f'Subject: Custom gear for {l["title"]} -- factory-direct pricing\n')
        f.write(f'From: HSN Warrior Apparels <hsnwarriorapparels@gmail.com>\n')
        f.write(f'To: {l["email"].split(",")[0].strip()}\n\n')
        f.write(body)

# Create IG DM drafts
with open('/home/ubuntu/gmaps-output/ig_dm_drafts.txt', 'w') as f:
    f.write('INSTAGRAM DM DRAFTS\n')
    f.write('=' * 60 + '\n\n')
    for l in leads:
        title = l['title']
        sport = 'wrestling' if 'wrestling' in l['title'].lower() else \
                'boxing' if 'boxing' in l['title'].lower() else \
                'BJJ' if any(x in l['title'].lower() for x in ['bjj', 'jiu jitsu', 'jiu-jitsu']) else \
                'Muay Thai' if 'muay thai' in l['title'].lower() else \
                'martial arts' if any(x in l['title'].lower() for x in ['martial arts', 'karate', 'taekwondo', 'kung fu']) else \
                'combat sports'
        dm = f'''Hi! Saw your club online -- impressive program. 

We're HSN Warrior Apparels, a custom fightwear manufacturer (since 2011). We make custom gear with your logo, colors & specs -- factory-direct, 10-piece minimum.

Same-day quote + mockup. Just reply with your logo/colors & quantities.

-- HSN Warrior Apparels
+92 337 3336381 | hsnwarriorapparels@gmail.com
hsnwarriorapparels.vercel.app'''

        f.write(f'CLUB: {l["title"]}\n')
        f.write(f'EMAIL: {l["email"]}\n')
        f.write(f'DM MESSAGE:\n{dm}\n')
        f.write('-' * 60 + '\n\n')

print('Created drafts and IG DM scripts for all leads')