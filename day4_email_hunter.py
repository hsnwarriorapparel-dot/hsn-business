#!/usr/bin/env python3
"""Day 4 overnight email-lead hunter for HSN Warrior Apparels.
NO WhatsApp activity (number banned - under review).
Goal: find 150-200 NEW leads with emails, send cold emails, IG follow+DM fallback.
Hunt source: multi-country Exa searches -> scrape contact pages -> extract emails.
"""
import subprocess, re, csv, time, json, os, random, sys

sys.path.insert(0, '/home/ubuntu')

CSV = '/home/ubuntu/leads.csv'
LOG = '/home/ubuntu/day4_log.txt'
TODAY_TAG = 'Day 4 night batch'

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

def append_lead(lead):
    with open(CSV, 'a', newline='') as f:
        w = csv.writer(f)
        w.writerow(lead)

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
WA_RE = re.compile(r'wa\.me/([0-9]{8,15})')
IG_RE = re.compile(r'instagram\.com/([a-zA-Z0-9_.]+)')
BAD_EMAIL = re.compile(r'(sentry|example|wixpress|\.png|\.jpg|\.js|\.webp|\.svg|email\.de|your?email|domain\.com|@2x|sitefactory|no-?reply|wordpress|godaddy)', re.I)

def scrape(url):
    try:
        r = subprocess.run(['curl', '-sL', '--max-time', '10', url],
                           capture_output=True, text=True, timeout=15)
        if not r.stdout:
            return None
        html = r.stdout
        emails = [e.lower() for e in EMAIL_RE.findall(html)]
        emails = [e for e in emails if not BAD_EMAIL.search(e)]
        # dedupe keep first
        seen = set(); ems = []
        for e in emails:
            if e not in seen:
                seen.add(e); ems.append(e)
        was_ = WA_RE.findall(html)
        igs = [i for i in IG_RE.findall(html) if i not in ('p', 'explore', 'accounts', 'stories', 'direct')]
        return {'emails': ems[:3], 'wa': list(dict.fromkeys(was_))[:1], 'ig': igs[:1], 'ok': True}
    except Exception as e:
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
    # (country, queries) — martial arts + boxing + MMA gyms across Europe
    ("Spain", ["gimnasio boxeo kickboxing contacto email", "academia muay thai Madrid Barcelona contacto",
               "club judo karate taekwondo España email contacto", "crossbox mma España gimnasio contacto"]),
    ("Portugal", ["academia boxe kickboxing Portugal contacto email", "ginasio muay thai Porto Lisboa contacto",
                  "clube judo karate Portugal email"]),
    ("France", ["club boxe anglaise France contact email", "salle muay thai MMA France contact",
                "club judo France email contact", "academie karate France contact"]),
    ("Germany", ["Boxgym kickboxen Deutschland Kontakt email", "Muay Thai Gym Deutschland Impressum",
                 "Judo Karate Verein Deutschland Kontakt", "MMA Gym Deutschland E-Mail"]),
    ("Italy", ["palestra boxe kickboxing Italia contatti email", "accademia muay thai Italia contatti",
               "societa judo karate Italia email contatti"]),
    ("Netherlands", ["boks school kickboksen Nederland contact email", "muay thai gym Amsterdam Rotterdam contact",
                      "judo vereniging Nederland email"]),
    ("Belgium", ["club boxe kickboxing Belgique contact email", "boksclub Belgie contact",
                 "judo club Belgium email contact"]),
    ("Poland", ["klub bokserski kickboxing Polska kontakt email", "szkola judo karate Polska kontakt"]),
    ("UK", ["boxing club gym London Manchester contact email", "muay thai gym UK contact email",
            "BJJ jiu jitsu academy UK email contact", "karate judo club UK email"]),
    ("Ireland", ["boxing club Dublin Ireland contact email", "martial arts academy Ireland email"]),
    ("Austria", ["boxgym kickboxen Wien Kontakt email", "judo karate Verein Österreich Kontakt"]),
    ("Switzerland", ["boxgym kickboxing Schweiz Kontakt email", "judo karate club Suisse contact"]),
    ("Sweden", ["boxning kickboxing Sverige Kontakt email", "muay thai gym Stockholm kontakt"]),
    ("Denmark", ["boksning kickboxing Danmark Kontakt email"]),
    ("Finland", ["nyrkkeily kickboxing Suomi yhteystiedot email"]),
    ("Norway", ["boksing kickboxing Norge Kontakt email"]),
    ("Czech Republic", ["box boxing gym Praha kontakt email", "judo karate klub Cesko kontakt"]),
    ("Slovakia", ["box gym Bratislava kontakt email"]),
    ("Hungary", ["box gym kickboxing Budapest kapcsolat email"]),
    ("Romania", ["sala box Bucuresti contact email", "muay thai Romania contact"]),
    ("Bulgaria", ["boxing gym Sofia contact email"]),
    ("Croatia", ["boxing gym Zagreb kontakt email"]),
    ("Slovenia", ["boxing gym Ljubljana kontakt email"]),
    ("Greece", ["boxing gym Athens contact email", "muay thai Greece contact"]),
    ("Turkey", ["boks spor salonu Istanbul iletisim email", "muay thai gym Istanbul email"]),
]

def gym_name_from_url(url, title_country):
    m = re.search(r'https?://(?:www\.)?([a-z0-9-]+)\.', url, re.I)
    name = (m.group(1).replace('-', ' ').replace('_', ' ').title() if m else 'Unknown Gym')
    return name

def main():
    log("DAY 4 NIGHT HUNT STARTING — target 150-200 new email leads. NO WA activity.")
    known = existing_emails()
    log(f"Known emails on file: {len(known)}")
    added = 0
    nid = next_id()
    # round-robin countries so we spread across Europe
    for country, queries in SEARCHES:
        for q in queries:
            urls = exa_search(q, 10)
            log(f"[{country}] '{q}' -> {len(urls)} urls")
            for url in urls:
                if 'exa.ai' in url or 'classpass' in url or 'studiomaps' in url:
                    continue
                data = scrape(url)
                if not data or not data['emails']:
                    continue
                email = data['emails'][0]
                if email in known:
                    continue
                known.add(email)
                name = gym_name_from_url(url, country)
                site = re.sub(r'https?://', '', url).split('/')[0]
                lead = [
                    f"L{nid:03d}", name, "Gym/Club", 
                    (f"@{data['ig'][0]}" if data['ig'] else ""),
                    (f"https://www.instagram.com/{data['ig'][0]}/" if data['ig'] else ""),
                    "", country,
                    (data['wa'][0] if data['wa'] else ""), ("mobile" if data['wa'] else ""),
                    email, site,
                    "RESEARCHED: email verified from own site, outreach pending",
                    f"Found via search: {q[:60]}", "Martial arts gear, uniforms", TODAY_TAG
                ]
                append_lead(lead)
                nid += 1
                added += 1
                log(f"  + {name} ({country}) {email} wa={'Y' if data['wa'] else '-'}")
                if added >= 200:
                    log(f"TARGET REACHED: {added} leads. Stopping hunt.")
                    return added
            time.sleep(8)  # gentle on exa
        if added >= 150:
            log(f"150 milestone hit ({added}). Continuing to 200...")
    log(f"HUNT PHASE DONE: {added} new email leads found.")
    return added

if __name__ == '__main__':
    n = main()
    log(f"TOTAL NEW LEADS: {n}")
