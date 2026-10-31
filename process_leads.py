import csv, json
from datetime import datetime
import os

with open('/home/ubuntu/gmaps-output/leads_day1_full_clean.json', 'r') as f:
    leads = json.load(f)

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
            title_lower = l['title'].lower()
            sport = 'wrestling' if 'wrestling' in title_lower else \
                    'boxing' if 'boxing' in title_lower else \
                    'BJJ' if any(x in title_lower for x in ['bjj', 'jiu jitsu', 'jiu-jitsu']) else \
                    'Muay Thai' if 'muay thai' in title_lower else \
                    'martial arts' if any(x in title_lower for x in ['martial arts', 'karate', 'taekwondo', 'kung fu']) else \
                    'combat sports'
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
                'READY_TO_SEND',
                '',
                'PENDING',
                '',
                'PENDING',
                '',
                'NO',
                '',
                'NEW',
                'Day 1 scrape - 137 clean leads'
            ])

# Create email drafts
os.makedirs('/home/ubuntu/gmaps-output/drafts', exist_ok=True)
for l in leads:
    title = l['title']
    email = l['email'].split(',')[0].strip()
    sport = 'wrestling' if 'wrestling' in l['title'].lower() else \
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