#!/usr/bin/env python3
"""Day-9 wave QA: fix junk-scraped names (derive real gym name from their own email/domain),
exclude contaminated/dead/federation rows. Row-targeted, atomic, read-back verified."""
import csv, os, tempfile

CSV = '/home/ubuntu/leads.csv'

# lead_id -> new Name (derived from the lead's own email/website/IG — no invention)
NAME_FIXES = {
 'L698': 'Kodokan 01',
 'L705': 'KBC Boxe Genova',
 'L711': 'Gotham Gym Bari',
 'L713': 'CFC Padova',
 'L714': 'SDM Team',
 'L716': 'Padova Top Team',
 'L717': 'MyClub Padova',
 'L719': 'Drago Blu',
 'L720': 'Speri Fight Club',
 'L721': 'Verona Boxing Fighters',
 'L723': 'Tempio degli Elfi',
 'L724': 'Centro Forma Evolution',
 'L726': 'Box Academy Stuttgart',
 'L729': 'Sturm Boxing',
 'L730': 'Uni Sport Hohenheim Boxen',
 'L731': 'Dragon Gym Stuttgart',
 'L733': 'MFA Gym',
 'L734': 'Red Tiger Club Duesseldorf',
 'L735': 'Boxklub Dresden',
 'L737': 'Kampfsportzentrum Dresden',
 'L739': 'Boxring Dresden',
 'L741': 'Training Hoch 3 Kampfsport',
 'L742': 'IS Double Touch Gym Dresden',
 'L743': 'Kick-Box Verein Leipzig',
 'L744': 'Boxring Atlas',
 'L745': 'Seiwakai Leipzig',
 'L746': 'Prisma Empowerment',
 'L748': 'Boxzentrum Nuernberg',
 'L749': 'Boxclub Almaz Nuernberg',
 'L752': 'The Gym Nuernberg',
 'L753': 'Boxenstop Nuernberg',
 'L754': 'Box-Club FCN',
 'L755': 'Kings Gym Hannover',
 'L757': 'Sticks and Stones',
 'L758': 'UFA Kampfsport',
 'L759': 'Fight Academy Groningen',
 'L760': 'Paulo Boer Muay Thai',
 'L761': 'Kickboxing Groningen',
 'L762': 'Bao Trieu Kung Fu',
 'L763': 'Renshu Fights',
 'L765': 'Muay Thai Gym Enschede',
 'L767': 'Sabah Boxeo Zaragoza',
 'L768': 'Gallar Box',
 'L769': 'Stadium Venecia',
 'L770': 'Karate Kan Zaragoza',
 'L771': 'Gimnasio Almozara',
 'L772': 'Arte Suave',
 'L774': 'Baan Kai Muay',
 'L777': 'Dragons Club',
 'L778': 'Fightland Alicante',
 'L780': 'Arena Alicante Boxing',
 'L782': 'SGO Wellness',
 'L786': 'In Legatum Vigo',
 'L787': 'Gimnasio Arena Vigo',
 'L788': 'Coliseum Vigo',
 'L789': 'Florida Gym Vigo',
 'L790': 'La Vieja Escuela Gym',
 'L791': 'Braga Open Boxing',
 'L707': 'Accademia Pugilistica Portoghese',
}

# lead_id -> exclusion reason (status marker; 'EXCLUDED' keeps them out of every future wave)
EXCLUSIONS = {
 'L700': 'EXCLUDED (Day 9 QA): constructed PEC address + website mismatch - contamination',
 'L702': 'EXCLUDED (Day 9 QA): placeholder email esempio@ilmiosito.com',
 'L704': 'EXCLUDED (Day 9 QA): parked domain ssdmtt.it',
 'L709': 'EXCLUDED (Day 9 QA): federation fpi.it - not a buyer',
 'L710': 'EXCLUDED (Day 9 QA): constructed PEC address + website mismatch - contamination',
 'L718': 'EXCLUDED (Day 9 QA): no live site gymup-city.it',
 'L736': 'EXCLUDED (Day 9 QA): email/site mismatch (taofit.de vs kampfsport-akademie.de)',
 'L781': 'EXCLUDED (Day 9 QA): dead domain academinalegiovii.com',
 'L784': 'EXCLUDED (Day 9 QA): federation fboxcv.com - not a buyer',
}

rows = list(csv.reader(open(CSV, newline='', encoding='utf-8')))
idx = {h: i for i, h in enumerate(rows[0])}
iN, iS = idx['Name'], idx['Status']

fixed_names = excluded = 0
for r in rows[1:]:
    lid = r[0].strip()
    if lid in NAME_FIXES:
        r[iN] = NAME_FIXES[lid]
        fixed_names += 1
    if lid in EXCLUSIONS:
        r[iS] = (r[iS].rstrip(' |') + ' | ' + EXCLUSIONS[lid])[:250]
        excluded += 1

fd, tmp = tempfile.mkstemp(dir='/home/ubuntu', suffix='.csv.tmp')
with os.fdopen(fd, 'w', newline='', encoding='utf-8') as f:
    csv.writer(f).writerows(rows)
os.replace(tmp, CSV)

# READ-BACK verification (mandatory)
rows2 = list(csv.reader(open(CSV, newline='', encoding='utf-8')))
assert len(rows2) == len(rows), f"row count changed! {len(rows)} -> {len(rows2)}"
idx2 = {h: i for i, h in enumerate(rows2[0])}
bad_names = [r[0] for r in rows2[1:] if r[idx2['Name']].strip().lower() in
             ('unknown gym', 'n/a', 'info', 'contactos', 'contact', 'contact us') ]
print(f"names fixed: {fixed_names} | excluded rows marked: {excluded}")
print(f"rows: {len(rows)} -> {len(rows2)} (verified)")
print("junk names remaining anywhere in file:", bad_names if bad_names else "NONE in wave check set")
# spot check
for r in rows2[1:]:
    if r[0] in ('L735', 'L752', 'L784', 'L702'):
        print("  check", r[0], "|", r[idx2['Name']], "|", r[idx2['Status']][:80])
