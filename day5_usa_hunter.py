#!/usr/bin/env python3
"""Day 5 USA hunter: find 200 USA martial arts / boxing / BJJ / MMA gym leads.
Extract emails + IG handles + WA numbers from their websites. NO sending here — hunter only.
Adapted from day4_email_hunter with USA-specific searches.
"""
import subprocess, re, csv, time, json, os, random, sys, tempfile

sys.path.insert(0, '/home/ubuntu')

CSV = '/home/ubuntu/leads.csv'
LOG = '/home/ubuntu/day5_log.txt'
TODAY_TAG = 'Day 5 USA batch'

def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + "\n")

def load_csv():
    with open(CSV) as f:
        return list(csv.reader(f))

def existing_emails():
    rows = load_csv()
    idx = {h: i for i, h in enumerate(rows[0])}
    return set((r[idx['Email']].strip().lower() for r in rows[1:] if r[idx['Email']].strip()))

def next_id():
    rows = load_csv()
    idx = {h: i for i, h in enumerate(rows[0])}
    return max(int(r[idx['Lead ID']][1:]) for r in rows[1:]) + 1

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
WA_RE = re.compile(r'wa\.me/([0-9]{8,15})')
IG_RE = re.compile(r'instagram\.com/([a-zA-Z0-9_.]+)')
BAD_EMAIL = re.compile(r'(sentry|example|wixpress|\.png|\.jpg|\.js|\.webp|\.svg|email\.de|your?email|domain\.com|@2x|no-?reply|wordpress|godaddy|squarespace|placeholder|sample@)', re.I)
BAD_DOMAIN = re.compile(r'(usaboxing\.org|teamusa|reddit|yelp|classpass|tripadvisor|thumbtack|facebook\.com/.*groups|meetup\.com|yellowpages|yelp\.com)', re.I)

def scrape(url):
    try:
        r = subprocess.run(['curl', '-sL', '--max-time', '10', url],
                           capture_output=True, text=True, timeout=15)
        if not r.stdout:
            return None
        html = r.stdout
        emails = [e.lower() for e in EMAIL_RE.findall(html)]
        emails = [e for e in emails if not BAD_EMAIL.search(e)]
        seen = set(); ems = []
        for e in emails:
            if e not in seen:
                seen.add(e); ems.append(e)
        was_ = WA_RE.findall(html)
        igs = [i for i in IG_RE.findall(html) if i not in ('p', 'explore', 'accounts', 'stories', 'direct', 'reel', 'reels')]
        return {'emails': ems[:3], 'wa': list(dict.fromkeys(was_))[:1], 'ig': igs[:1], 'ok': True}
    except Exception:
        return None

def exa_search(query, n=10):
    cmd = ['timeout', '70', 'mcporter', 'call', f'exa.web_search_exa(query: "{query}", numResults: {n})']
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=80)
        urls = re.findall(r'URL: (\S+)', r.stdout)
        return urls
    except Exception:
        return []

SEARCHES = [
    ("USA", ["boxing gym New York contact email", "boxing gym Los Angeles Chicago contact email",
             "muay thai gym Miami Houston Dallas contact", "MMA gym Phoenix Philadelphia Denver contact email",
             "BJU jiu jitsu academy Seattle Portland contact", "mixed martial arts academy Atlanta Boston email",
             "kickboxing gym Las Vegas Detroit contact", "wrestling judo karate school USA contact email",
             "martial arts school franchise USA email contact", "fight team boxing club USA contact email",
             "taekwondo school Texas Florida contact email", "grappling academy USA email contact",
             "boxing training gym San Francisco contact", "combat sports gym Washington DC contact email"]),
    ("USA", ["smalls boxing gym email contact", "local MMA training center email",
             "jiu jitsu association gym members email contact", "boxing fitness club USA contact",
             "self defense training center email USA", "kickboxing fitness studio contact email USA",
             "youth boxing program gym contact email", "amateur boxing club email USA",
             "crossfit box gym combat contact email", "college wrestling club contact email",
             "police military training gym contact email", "professional boxing gym email contact"]),
]

def gym_name_from_url(url):
    m = re.search(r'https?://(?:www\.)?([a-z0-9-]+)\.', url, re.I)
    return m.group(1).replace('-', ' ').replace('_', ' ').title() if m else 'US Gym'

def main():
    log("DAY 5 USA HUNT START — target 200 new email leads")
    known = existing_emails()
    log(f"Known emails: {len(known)}")
    added = 0
    nid = next_id()
    for country, queries in SEARCHES:
        for q in queries:
            urls = exa_search(q, 10)
            log(f"[USA] '{q}' -> {len(urls)} urls")
            for url in urls:
                if 'exa.ai' in url or BAD_DOMAIN.search(url):
                    continue
                data = scrape(url)
                if not data or not data['emails']:
                    continue
                email = data['emails'][0]
                if email in known:
                    continue
                known.add(email)
                name = gym_name_from_url(url)
                site = re.sub(r'https?://', '', url).split('/')[0]
                lead = [
                    f"L{nid:03d}", name, "Gym/Club",
                    (f"@{data['ig'][0]}" if data['ig'] else ""),
                    (f"https://www.instagram.com/{data['ig'][0]}/" if data['ig'] else ""),
                    "", country,
                    (data['wa'][0] if data['wa'] else ""), ("mobile" if data['wa'] else ""),
                    email, site,
                    "RESEARCHED: USA lead, outreach pending",
                    f"Found via: {q[:50]}", "Martial arts gear, uniforms", TODAY_TAG
                ]
                # append via safe pattern: read fresh, append, write temp, verify, replace
                rows = load_csv()
                rows.append(lead)
                fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
                with os.fdopen(fd, 'w', newline='') as f:
                    csv.writer(f).writerows(rows)
                with open(tmp) as f:
                    check = list(csv.reader(f))
                assert len(check) == len(rows)
                os.replace(tmp, CSV)
                nid += 1
                added += 1
                log(f"  + {name} ({email}) wa={'Y' if data['wa'] else '-'} ig={'Y' if data['ig'] else '-'}")
                if added >= 200:
                    log(f"TARGET REACHED: {added}")
                    return added
            time.sleep(8)
    log(f"HUNT DONE: {added} USA leads")
    return added

if __name__ == '__main__':
    n = main()
    log(f"TOTAL NEW USA LEADS: {n}")
