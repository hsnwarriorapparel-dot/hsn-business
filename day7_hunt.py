#!/usr/bin/env python3
"""Day 7 hunter: Exa round-robin EU/UK/USA martial-arts gym leads -> emails.
Stops when CSV ammo (email, not sent, not failed) >= TARGET.
Writes PROPER 15-col rows (day6 bug wrote 18 cols). Skips federations,
directories, and generic webmail per the nightly task spec."""
import subprocess, re, csv, time, os, sys, html as ihtml

CSV = '/home/ubuntu/leads.csv'
LOG = '/home/ubuntu/day7_hunt_log.txt'
TARGET = 101
TODAY_TAG = 'Hunted Day 7 (2026-10-19)'

def log(m):
    line = time.strftime('%H:%M:%S') + ' ' + m
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')

def load_csv():
    with open(CSV, newline='', encoding='utf-8-sig') as f:
        return list(csv.reader(f))

IDX = {h: i for i, h in enumerate(load_csv()[0])}

def ammo_count():
    rows = load_csv()
    n = 0
    for r in rows[1:]:
        st = (r[IDX['Status']] or '').lower()
        if (r[IDX['Email']] or '').strip() and 'email sent' not in st and 'failed' not in st:
            n += 1
    return n

def known_emails_phones():
    rows = load_csv()
    ems = {(r[IDX['Email']] or '').strip().lower() for r in rows[1:] if r[IDX['Email']].strip()}
    phs = {re.sub(r'\D', '', r[IDX['Phone']] or '') for r in rows[1:] if (r[IDX['Phone']] or '').strip()}
    return ems, phs

def next_id():
    rows = load_csv()
    return max(int(r[0][1:]) for r in rows[1:]) + 1

def append_lead(lead):
    with open(CSV, 'a', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow(lead)

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
WA_RE = re.compile(r'wa\.me/(\d{8,15})')
IG_RE = re.compile(r'instagram\.com/([a-zA-Z0-9_.]{3,30})')

BAD_EMAIL = re.compile(r'(sentry|wixpress|example|wix\.|squarespace|\.png|\.jpe?g|\.js|\.webp|\.svg|\.gif|\.css|'
                       r'email\.de|your?email|domain\.com|@2x|sitefactory|no-?reply|wordpress|godaddy|'
                       r'\.dewww|klarna|shopify|cloudflare|\.js\?|schema\.org)', re.I)
WEBMAIL = re.compile(r'@(gmail|hotmail|yahoo|gmx|outlook|live|icloud|msn|aol|proton|me\.com|googlemail)\.', re.I)
BAD_DOMAIN = ['ffjudo', 'ffkarate', 'fijlkam', 'judobund', 'wako', 'britishjudo', 'ffboxe',
              'kickboxen-deutschland', 'fkb.nl', 'usaboxing', 'trouver-un-club', 'kombazen', 'ffsavate',
              'judoinside', 'reddit', 'yelp', 'classpass', 'meetup', 'yellowpages', 'tripadvisor',
              'thumbtack', 'teamusa', 'studiomaps', 'exa.ai', 'facebook.', 'wikipedia', 'youtube',
              'threads.net', 'tiktok', 'linktr.ee', 'columbus.ee']

def clean_name(t):
    t = ihtml.unescape(t or '')
    t = re.sub(r'\s+', ' ', t).strip()
    for sep in [' | ', ' – ', ' — ', ' - ']:
        if sep in t:
            t = t.split(sep)[0]
    t = t.strip(' -|–·')
    for suf in ['kontakt', 'contact', 'impressum', 'home', 'contatti', 'contacto', 'über uns']:
        if t.lower().endswith(' ' + suf) or t.lower() == suf:
            t = t[: -(len(suf) + 1)].strip()
    return t[:45].strip() or 'Unknown Gym'

def norm_email(e):
    e = (e or '').strip()
    e = re.sub(r'^(%20|u00a0|\\u00a0|\s)+', '', e, flags=re.I)
    return e.lower().strip('.,;:()<>')

def valid_email(e):
    if not e or e.count('@') != 1 or len(e) > 60:
        return False
    dom = e.rsplit('@', 1)[1]
    if '.' not in dom or not re.fullmatch(r'[a-z]{2,}', dom.rsplit('.', 1)[1]):
        return False
    if BAD_EMAIL.search(e) or WEBMAIL.search(e):
        return False
    return True

def curl(url):
    try:
        r = subprocess.run(['curl', '-sL', '--max-time', '12', '-A',
                            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                            url], capture_output=True, text=True, timeout=18)
        return r.stdout or ''
    except Exception:
        return ''

def exa_search(query, n=10):
    cmd = ['timeout', '70', 'mcporter', 'call', f'exa.web_search_exa(query: "{query}", numResults: {n})']
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=80)
        blocks = re.split(r'\n(?=Title: )', r.stdout)
        out = []
        for b in blocks:
            mu = re.search(r'URL: (\S+)', b)
            mt = re.search(r'Title: (.+)', b)
            if not mu:
                continue
            url = mu.group(1).strip()
            if any(d in url.lower() for d in BAD_DOMAIN):
                continue
            title = mt.group(1).strip() if mt else url
            out.append((title, url, b))
        return out
    except Exception as e:
        log(f"  exa err: {str(e)[:50]}")
        return []

# (country, city, query) — EU heavy + USA per task spec
QUERIES = [
    ("Italy", "Milano", "palestra boxe Milano contatti email"),
    ("Italy", "Roma", "boxing gym Roma contatto email"),
    ("Italy", "Torino", "pugilato Torino palestra contatti"),
    ("Italy", "Napoli", "muay thai Napoli palestra email"),
    ("Germany", "München", "Boxgym München Kontakt E-Mail"),
    ("Germany", "Berlin", "Boxschule Berlin Kontakt email"),
    ("Germany", "Hamburg", "Muay Thai Gym Hamburg Impressum email"),
    ("Germany", "Frankfurt", "MMA Gym Frankfurt Kontakt E-Mail"),
    ("Germany", "Köln", "Kickboxen Köln Verein Kontakt email"),
    ("Netherlands", "Amsterdam", "boksport Amsterdam contact email"),
    ("Netherlands", "Rotterdam", "kickboksen Rotterdam contact email"),
    ("Netherlands", "Eindhoven", "muay thai Eindhoven contact email"),
    ("Spain", "Madrid", "boxeo Madrid gimnasio contacto email"),
    ("Spain", "Barcelona", "boxing gym Barcelona contacto email"),
    ("Spain", "Valencia", "muay thai Valencia gimnasio contacto"),
    ("Spain", "Sevilla", "kickboxing Sevilla gimnasio email contacto"),
    ("Portugal", "Lisboa", "academia boxe Lisboa contacto email"),
    ("Portugal", "Porto", "muay thai Porto academia contacto"),
    ("France", "Paris", "club boxe Paris contact email"),
    ("France", "Lyon", "muay thai Lyon salle contact email"),
    ("France", "Marseille", "boxe anglaise Marseille club contact"),
    ("France", "Lille", "MMA Lille salle contact email"),
    ("UK", "London", "boxing gym London contact email"),
    ("UK", "Manchester", "muay thai gym Manchester contact email"),
    ("UK", "Birmingham", "boxing club Birmingham contact email"),
    ("UK", "Leeds", "MMA gym Leeds contact email"),
    ("UK", "Glasgow", "boxing gym Glasgow contact email"),
    ("UK", "Bristol", "kickboxing Bristol club contact email"),
    ("Ireland", "Dublin", "boxing club Dublin contact email"),
    ("Ireland", "Cork", "martial arts Cork contact email"),
    ("Belgium", "Brussel", "boksclub Brussel contact email"),
    ("Austria", "Wien", "Boxgym Wien Kontakt email"),
    ("Switzerland", "Zürich", "Boxgym Zürich Kontakt email"),
    ("Sweden", "Stockholm", "boxning Stockholm kontakt email"),
    ("Denmark", "København", "boksning København kontakt email"),
    ("Norway", "Oslo", "boksing Oslo kontakt email"),
    ("Finland", "Helsinki", "nyrkkeily Helsinki yhteystiedot email"),
    ("Poland", "Warszawa", "klub bokserski Warszawa kontakt email"),
    ("Poland", "Kraków", "muay thai Kraków klub kontakt"),
    ("Czech Republic", "Praha", "boxing gym Praha kontakt email"),
    ("Hungary", "Budapest", "boxing gym Budapest kapcsolat email"),
    ("Greece", "Athens", "boxing gym Athens contact email"),
    ("USA", "Texas", "boxing gym Texas contact email"),
    ("USA", "California", "MMA gym California contact email"),
    ("USA", "Florida", "boxing gym Florida contact email"),
    ("USA", "New York", "MMA gym New York contact email"),
    ("USA", "Illinois", "boxing gym Chicago contact email"),
    ("USA", "Georgia", "MMA gym Atlanta Georgia contact email"),
    ("USA", "Arizona", "muay thai gym Arizona contact email"),
]

def main():
    log(f"DAY 7 HUNT START — ammo now {ammo_count()}, target {TARGET}")
    known, known_phones = known_emails_phones()
    nid = next_id()
    added = 0
    for country, city, q in QUERIES:
        if ammo_count() >= TARGET:
            log(f"TARGET REACHED (ammo {ammo_count()}). Stopping.")
            break
        results = exa_search(q, 10)
        log(f"[{country}/{city}] '{q}' -> {len(results)} usable results")
        for title, url, block in results:
            if ammo_count() >= TARGET:
                break
            # emails from Exa highlights text first (works when curl is blocked)
            emails = [norm_email(e) for e in EMAIL_RE.findall(block)]
            html = ''
            igs, was_ = [], []
            if len([e for e in emails if valid_email(e)]) == 0:
                html = curl(url)
                emails += [norm_email(e) for e in EMAIL_RE.findall(html)]
                was_ = list(dict.fromkeys(WA_RE.findall(html)))[:1]
                igs = [i for i in IG_RE.findall(html)
                       if i.lower() not in ('p', 'explore', 'accounts', 'stories', 'direct', 'reel', 'squarespace', 'wix', 'embed')][:1]
            emails = [e for e in dict.fromkeys(emails) if valid_email(e)]
            if not emails:
                continue
            email = emails[0]
            if email in known:
                continue
            known.add(email)
            name = clean_name(title)
            site = re.sub(r'https?://(www\.)?', '', url).split('/')[0]
            lead = [''] * 15
            lead[IDX['Lead ID']] = f"L{nid:03d}"
            lead[IDX['Name']] = name
            lead[IDX['Type']] = 'Gym/Club'
            lead[IDX['IG Username']] = (f"@{igs[0]}" if igs else '')
            lead[IDX['IG Profile Link']] = (f"https://www.instagram.com/{igs[0]}/" if igs else '')
            lead[IDX['City']] = city
            lead[IDX['Country']] = country
            lead[IDX['Phone']] = (was_[0] if was_ else '')
            lead[IDX['Phone Type']] = 'mobile' if was_ else ''
            lead[IDX['Email']] = email
            lead[IDX['Website']] = site
            lead[IDX['Status']] = 'HUNTED Day 7'
            lead[IDX['Profile Analysis']] = f"Found via search: {q[:55]}"
            lead[IDX['Products Needed']] = 'Martial arts gear, uniforms'
            lead[IDX['Notes']] = TODAY_TAG
            append_lead(lead)
            nid += 1
            added += 1
            log(f"  + L{nid-1:03d} {name[:32]} ({country}) {email} wa={'Y' if was_ else '-'} ig={'@'+igs[0] if igs else '-'}")
            time.sleep(1)
        time.sleep(8)
    # final readback
    rows = load_csv()
    bad = [r[0] for r in rows[1:] if len(r) != 15]
    log(f"HUNT DONE: +{added} leads | CSV rows {len(rows)-1} | last ID {rows[-1][0]} | bad-col rows {len(bad)} | ammo {ammo_count()}")
    return added

if __name__ == '__main__':
    main()
