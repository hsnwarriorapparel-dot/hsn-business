#!/usr/bin/env python3
"""Spam-word-check the rendered email templates against spam-word-checker rules."""
import sys, re
sys.path.insert(0, '/home/ubuntu')
import templates

BANNED_WORDS = ['get','bank','credit','access','open','compare','problem','now',
 'billing','deal','finance','financial','claims','insurance','mortgage','soon',
 'new','performance','freedom','home','sales','medical','urgent','life','marketing',
 'investment','diagnostics','friend','cash','invoice','extra','purchase']

BANNED_PHRASES = ['off chance','one time','all good','following up here',
 'last note from me here','great fit','bumping this once','just following up once',
 'circle back','one more quick follow-up','keep this open','compare notes',
 'compare notes live','appreciate the reply']

RISKY = ['$$$','50% off','100% guaranteed','100% free','100% off','act fast',
 'act immediately','act now','action required','affordable deal','amazing',
 'apply here','apply now','best bargain','best deal','best offer','best price',
 'best rates','big profit','bonus','buy now','buy today','call now','click',
 'click below','click here','click this link','contact us immediately',
 'deal ending soon','discount','don\'t delete','double your money','earn',
 'exclusive deal','expires today','fantastic','fast cash','final call','for free',
 'free access','free consultation','free gift','free membership','free money',
 'free quote','free trial','full refund','get it now','giveaway','great news',
 'guaranteed deposit','guaranteed results','hurry up','immediately',
 'increase revenue','increase sales','instant earnings','limited time',
 'lowest price','make money','must read','no cost','no obligation','now',
 'offer now','order now','order today','please read','price protection',
 'profits','promise','pure profit','quote','risk-free','satisfaction guaranteed',
 'save $','save big money','sign up free','special invitation','special offer',
 'special promotion','take action now','the best','this won\'t last','thousands',
 'time limited','today','trial','unbeatable offer','unbelievable','unlimited',
 'urgent','what are you waiting for?','while supplies last','why pay more?',
 'winner announced','wonderful','you are a winner','you will not believe']

PHRASING = ['access your account','account update','activate now','change password',
 'click to verify','confirm your details','data breach','download now','final notice',
 'important update','install now','last warning','log in now','password reset',
 'payment details needed','phishing alert','security breach','security update',
 'update account','verify identity','warning message']


def check(label, text):
    low = text.lower()
    hits = []
    for w in BANNED_WORDS:
        # token match with word boundary, allows compounds to be caught
        if re.search(r'(?<![a-z])' + re.escape(w) + r'(?![a-z])', low):
            hits.append('WORD:' + w)
    for p in BANNED_PHRASES + RISKY + PHRASING:
        if p in low:
            hits.append('PHRASE:' + p)
    if '—' in text:
        hits.append('EM-DASH')
    if re.search(r'\b[A-Z]{4,}\b', text):
        # allow brand/known acronyms
        bad = [m for m in re.findall(r'\b[A-Z]{4,}\b', text)
               if m not in ('HSN', 'OEM', 'BJJ', 'MMA')]
        if bad:
            hits.append('ALLCAPS:' + ','.join(bad[:3]))
    if re.search(r'!!', text):
        hits.append('MULTI-EXCL')
    if re.match(r'^\s*(hi|hello|hey)\b', low):
        hits.append('GREETING-PREFIX')
    print(f'--- {label} ---')
    print('  HITS:', hits if hits else 'CLEAN')
    return hits


allhits = []
for region in ('USA', 'Europe'):
    for name, detail in (('Test Gym Team', 'martial arts and boxing gym in Chicago'),
                         ('Atelier Boxe', 'martial arts and boxing gym in Lyon')):
        s, b = templates.build_email(name, detail, region=region)
        allhits += check(f'{region} | {name} | subject', s)
        allhits += check(f'{region} | {name} | body', b)

print()
print('TOTAL HITS:', len(allhits))
