#!/usr/bin/env python3
"""Day 8 hunter: Exa round-robin FRESH EU/UK/USA cities -> gym emails.
Stops when pipeline-eligible ammo (email, not sent, not failed, not active)
>= 100. 15-col rows, federation/directory/webmail filters, country-prefix
contamination guard on wa.me numbers, dedupe vs existing emails."""
import subprocess, re, csv, time, os, html as ihtml

CSV = '/home/ubuntu/leads.csv'
LOG = '/home/ubuntu/day8_hunt_log.txt'
TARGET = 100
TODAY_TAG = 'Hunted Day 8 (2026-10-21)'

def log(m):
    line = time.strftime('%H:%M:%S') + ' ' + m
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')

def load_csv():
    with open(CSV, newline='', encoding='utf-8') as f:
        return list(csv.reader(f))

IDX = {h: i for i, h in enumerate(load_csv()[0])}
ACTIVE = ['follow-up', 'hot lead', 'negotiat', 'sample quote', 'awaiting']

def ammo_count():
    rows = load_csv()
    n = 0
    for r in rows[1:]:
        st = (r[IDX['Status']] or '').lower()
        if not (r[IDX['Email']] or '').strip():
            continue
        if 'email sent' in st or 'failed' in st or 're-hunt' in st:
            continue
        if any(m in st for m in ACTIVE):
            continue
        n += 1
    return n

def known_emails_phones():
    rows = load_csv()
    ems = {(r[IDX['Email']] or '').strip().lower() for r in rows[1:] if r[IDX['Email']].strip()}
    phs = {re.sub(r'\D', '', r[IDX['Phone']] or '') for r in rows[1:] if (r[IDX['Phone']] or '').strip()}
    return ems, phs

def next_id():
    rows = load_csv()
    return max(int(r[0][1:]) for r in rows[1:] if r[0].startswith('L') and r[0][1:].isdigit()) + 1

def append_lead(lead):
    with open(CSV, 'a', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow(lead)

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
WA_RE = re.compile(r'wa\.me/(\d{8,15})')
IG_RE = re.compile(r'instagram\.com/([a-zA-Z0-9_.]{3,30})')

BAD_EMAIL = re.compile(r'(sentry|wixpress|example|wix\.|squarespace|\.png|\.jpe?g|\.js|\.webp|\.svg|\.gif|\.css|'
                       r'email\.de|your?email|domain\.com|@2x|sitefactory|no-?reply|wordpress|godaddy|'
                       r'\.dewww|klarna|shopify|cloudflare|\.js\?|schema\.org|\.png|abstract|polyfill)', re.I)
WEBMAIL = re.compile(r'@(gmail|hotmail|yahoo|gmx|outlook|live|icloud|msn|aol|proton|me\.com|googlemail)\.', re.I)
BAD_DOMAIN = ['ffjudo', 'ffkarate', 'fijlkam', 'judobund', 'wako', 'britishjudo', 'ffboxe',
              'kickboxen-deutschland', 'fkb.nl', 'usaboxing', 'trouver-un-club', 'kombazen', 'ffsavate',
              'judoinside', 'reddit', 'yelp', 'classpass', 'meetup', 'yellowpages', 'tripadvisor',
              'thumbtack', 'teamusa', 'studiomaps', 'exa.ai', 'facebook.', 'wikipedia', 'youtube',
              'threads.net', 'tiktok', 'linktr.ee', 'columbus.ee', 'trustpilot', 'bannergress',
              'care.com', 'indenpro', 'booksy', 'mindbody', 'gymline']

# country -> acceptable wa.me/phone prefixes (contamination guard)
PREFIX = {'Spain': ['34'], 'Portugal': ['351'], 'Italy': ['39'], 'France': ['33'],
          'UK': ['44'], 'Germany': ['49'], 'Switzerland': ['41'], 'Netherlands': ['31'],
          'Ireland': ['353'], 'Belgium': ['32'], 'Austria': ['43'], 'Sweden': ['46'],
          'Denmark': ['45'], 'Norway': ['47'], 'Finland': ['358'], 'Poland': ['48'],
          'Czech Republic': ['420'], 'Hungary': ['36'], 'Greece': ['30'], 'USA': ['1']}

JUNK_IG = {'p', 'explore', 'accounts', 'stories', 'direct', 'reel', 'reels', 'squarespace',
           'wix', 'embed', 'instagram', 'facebook', 'google', 'youtube', 'mail', 'share',
           'jiujitsudotcom', 'gymshark', 'tiptoe', 'static', 'about'}

def clean_name(t):
    t = ihtml.unescape(t or '')
    t = re.sub(r'\s+', ' ', t).strip()
    for sep in [' | ', ' – ', ' — ', ' - ']:
        if sep in t:
            t = t.split(sep)[0]
    t = t.strip(' -|–·')
    for suf in ['kontakt', 'contact', 'impressum', 'home', 'contatti', 'contacto', 'über uns',
                'email', 'e-mail', 'contatti e orari']:
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

# FRESH cities only (day7 already mined Milano/Roma/München/Berlin/etc.)
QUERIES = [
    ("Italy", "Bologna", "palestra boxe Bologna contatti email"),
    ("Italy", "Firenze", "muay thai Firenze palestra email"),
    ("Italy", "Genova", "MMA Genova palestra contatti email"),
    ("Italy", "Bari", "pugilato Bari palestra contatti email"),
    ("Italy", "Padova", "kickboxing Padova palestra contatti email"),
    ("Italy", "Verona", "boxe Verona palestra contatti email"),
    ("Germany", "Stuttgart", "Boxgym Stuttgart Kontakt E-Mail"),
    ("Germany", "Düsseldorf", "MMA Gym Düsseldorf Kontakt email"),
    ("Germany", "Dresden", "Boxschule Dresden Kontakt E-Mail"),
    ("Germany", "Leipzig", "Kickboxen Leipzig Verein Kontakt email"),
    ("Germany", "Nürnberg", "Boxgym Nürnberg Kontakt E-Mail"),
    ("Germany", "Hannover", "Muay Thai Gym Hannover Kontakt email"),
    ("Germany", "Bremen", "Boxschule Bremen Kontakt E-Mail"),
    ("Germany", "Münster", "MMA Gym Münster Kontakt email"),
    ("Netherlands", "Utrecht", "boksclub Utrecht contact email"),
    ("Netherlands", "Den Haag", "kickboksen Den Haag contact email"),
    ("Netherlands", "Groningen", "muay thai Groningen contact email"),
    ("Spain", "Zaragoza", "boxeo Zaragoza gimnasio contacto email"),
    ("Spain", "Bilbao", "muay thai Bilbao gimnasio contacto email"),
    ("Spain", "Málaga", "MMA Málaga gimnasio email contacto"),
    ("Spain", "Murcia", "kickboxing Murcia gimnasio contacto"),
    ("Spain", "Alicante", "boxing gym Alicante contacto email"),
    ("Spain", "Vigo", "boxeo Vigo gimnasio contacto email"),
    ("Portugal", "Braga", "academia boxe Braga contacto email"),
    ("Portugal", "Coimbra", "muay thai Coimbra academia contacto"),
    ("Portugal", "Faro", "MMA Faro academia contacto email"),
    ("France", "Toulouse", "club boxe Toulouse contact email"),
    ("France", "Bordeaux", "muay thai Bordeaux salle contact email"),
    ("France", "Nantes", "MMA Nantes salle contact email"),
    ("France", "Strasbourg", "boxe anglaise Strasbourg club contact email"),
    ("France", "Montpellier", "kickboxing Montpellier salle email"),
    ("France", "Rennes", "club boxe Rennes contact email"),
    ("France", "Nice", "muay thai Nice salle contact email"),
    ("France", "Grenoble", "MMA Grenoble salle contact email"),
    ("UK", "Liverpool", "boxing gym Liverpool contact email"),
    ("UK", "Newcastle", "boxing gym Newcastle contact email"),
    ("UK", "Sheffield", "boxing club Sheffield contact email"),
    ("UK", "Nottingham", "MMA gym Nottingham contact email"),
    ("UK", "Cardiff", "muay thai gym Cardiff contact email"),
    ("UK", "Edinburgh", "boxing gym Edinburgh contact email"),
    ("UK", "Leicester", "kickboxing Leicester club contact email"),
    ("UK", "Coventry", "boxing gym Coventry contact email"),
    ("Ireland", "Galway", "boxing club Galway contact email"),
    ("Ireland", "Limerick", "Muay Thai Limerick contact email"),
    ("Belgium", "Antwerpen", "boksclub Antwerpen contact email"),
    ("Belgium", "Gent", "muay thai Gent contact email"),
    ("Belgium", "Liège", "club boxe Liège contact email"),
    ("Switzerland", "Basel", "Boxgym Basel Kontakt email"),
    ("Switzerland", "Lausanne", "boxe Lausanne salle contact email"),
    ("Switzerland", "Bern", "MMA Bern Training Kontakt email"),
    ("Austria", "Graz", "Boxgym Graz Kontakt email"),
    ("Austria", "Salzburg", "Muay Thai Salzburg Kontakt email"),
    ("Austria", "Innsbruck", "Boxschule Innsbruck Kontakt E-Mail"),
    ("Sweden", "Göteborg", "boxning Göteborg kontakt email"),
    ("Sweden", "Malmö", "MMA Malmö kontakt email"),
    ("Denmark", "Aarhus", "boksning Aarhus kontakt email"),
    ("Poland", "Wrocław", "klub bokserski Wrocław kontakt email"),
    ("Poland", "Gdańsk", "muay thai Gdańsk klub kontakt email"),
    ("Poland", "Poznań", "MMA Poznań klub kontakt email"),
    ("USA", "Houston", "boxing gym Houston Texas contact email"),
    ("USA", "Dallas", "MMA gym Dallas contact email"),
    ("USA", "Austin", "muay thai gym Austin Texas contact email"),
    ("USA", "San Diego", "boxing gym San Diego contact email"),
    ("USA", "Phoenix", "MMA gym Phoenix Arizona contact email"),
    ("USA", "Denver", "boxing gym Denver contact email"),
    ("USA", "Seattle", "MMA gym Seattle contact email"),
    ("USA", "Boston", "boxing gym Boston contact email"),
    ("USA", "Philadelphia", "MMA gym Philadelphia contact email"),
    ("USA", "Washington DC", "boxing gym Washington DC contact email"),
    ("USA", "Nashville", "MMA gym Nashville contact email"),
    ("USA", "Charlotte", "boxing gym Charlotte NC contact email"),
    ("USA", "Minneapolis", "MMA gym Minneapolis contact email"),
    ("USA", "Las Vegas", "boxing gym Las Vegas contact email"),
    ("USA", "Miami", "MMA gym Miami contact email"),
]

def main():
    log(f"DAY 8 HUNT START — eligible ammo {ammo_count()}, target {TARGET}")
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
            emails = [norm_email(e) for e in EMAIL_RE.findall(block)]
            html = ''
            igs, was_ = [], []
            if len([e for e in emails if valid_email(e)]) == 0:
                html = curl(url)
                emails += [norm_email(e) for e in EMAIL_RE.findall(html)]
                was_ = list(dict.fromkeys(WA_RE.findall(html)))[:1]
                igs = [i for i in IG_RE.findall(html)
                       if i.lower() not in JUNK_IG][:1]
            emails = [e for e in dict.fromkeys(emails) if valid_email(e)]
            if not emails:
                continue
            email = emails[0]
            if email in known:
                continue
            # contamination guard: wa.me prefix must match the country
            ph = ''
            if was_:
                d = re.sub(r'\D', '', was_[0])
                pref = PREFIX.get(country)
                if pref and any(d.startswith(x) for x in pref) and len(d) >= 11:
                    ph = d
            ig = ''
            if igs and igs[0].lower() not in JUNK_IG:
                ig = igs[0]
            known.add(email)
            name = clean_name(title)
            site = re.sub(r'https?://(www\.)?', '', url).split('/')[0]
            lead = [''] * 15
            lead[IDX['Lead ID']] = f"L{nid:03d}"
            lead[IDX['Name']] = name
            lead[IDX['Type']] = 'Gym/Club'
            lead[IDX['IG Username']] = (f"@{ig}" if ig else '')
            lead[IDX['IG Profile Link']] = (f"https://www.instagram.com/{ig}/" if ig else '')
            lead[IDX['City']] = city
            lead[IDX['Country']] = country
            lead[IDX['Phone']] = ph
            lead[IDX['Phone Type']] = 'mobile' if ph else ''
            lead[IDX['Email']] = email
            lead[IDX['Website']] = site
            lead[IDX['Status']] = 'HUNTED Day 8'
            lead[IDX['Profile Analysis']] = f"Found via search: {q[:55]}"
            lead[IDX['Products Needed']] = 'Martial arts gear, uniforms'
            lead[IDX['Notes']] = TODAY_TAG
            append_lead(lead)
            nid += 1
            added += 1
            log(f"  + L{nid-1:03d} {name[:32]} ({country}) {email} wa={'Y' if ph else '-'} ig={'@'+ig if ig else '-'}")
            time.sleep(1)
        time.sleep(8)
    rows = load_csv()
    bad = [r[0] for r in rows[1:] if len(r) != 15]
    log(f"HUNT DONE: +{added} leads | CSV rows {len(rows)-1} | last ID {rows[-1][0]} | bad-col rows {len(bad)} | ammo {ammo_count()}")
    return added

if __name__ == '__main__':
    main()
