#!/usr/bin/env python3
"""Message templates for HSN Warrior Apparels outreach.
Company: HSN Warrior Apparels | Phone: +92 337 3336381 | NO free samples.
Sign-off: company name only (no personal name)."""
import random

COMPANY = "HSN Warrior Apparels"
PHONE = "+92 337 3336381"
EMAIL = "hsnwarriorapparel@gmail.com"

# Spanish gym/club DM openers (varied so no two leads get the same message)
# Spam rules applied (spam-word-checker): no greeting prefix before the first
# name (no Hi/Hello/Hey) and no em dashes anywhere in outbound copy.
DM_OPENERS = [
    "{name}! 👋 We're {company}, martial arts and sportswear manufacturers from Sialkot working with clubs worldwide.",
    "{name} 👋 {company} here, we manufacture martial arts gear and custom team wear in Sialkot.",
    "{name}! 👋 {company} here, we produce uniforms, gis and fight gear for clubs and schools worldwide.",
    "{name}! We're {company}, manufacturers of martial arts apparel. Just found your page, great work! 👏",
    "From {company} 👋, we make custom martial arts gear and team wear for clubs like yours.",
]

DM_MID = [
    "Saw your {detail}, really solid program you've built.",
    "Been checking out your {detail}, impressive!",
    "Your {detail} caught our eye, nice community you have.",
    "Love what you're doing with {detail}!",
]

DM_OFFERS = [
    "We do OEM/private label production: uniforms, gloves and team wear with your club's branding, factory-direct with small minimums.",
    "We offer private-label manufacturing: gear and uniforms with your own branding, direct from our factory. Low minimums for clubs.",
    "Our specialty is custom club gear: your branding on uniforms, gis and fight equipment, at manufacturer prices with club-friendly minimums.",
    "We produce branded uniforms and equipment for clubs: your logo, our factory, small order quantities welcome.",
]

DM_CTAS = [
    "Would the catalog + wholesale price list be useful for you?",
    "Interested in seeing our catalog and club pricing?",
    "Can I send over our catalog and wholesale list?",
    "Want me to share our catalog + prices for clubs?",
]

EMAIL_SUBJECTS = [
    "Custom martial arts gear for {name} - {company}",
    "{company} - club gear manufacturing for {name}",
    "Branded uniforms & equipment for {name}",
    "{name} x {company} - custom club apparel",
]

def build_dm(name, detail):
    o = random.choice(DM_OPENERS).format(name=name, company=COMPANY)
    m = random.choice(DM_MID).format(detail=detail)
    f = random.choice(DM_OFFERS)
    c = random.choice(DM_CTAS)
    return f"{o}\n\n{m} {f}\n\n{c}"

def build_wa(name, detail):
    o = random.choice(DM_OPENERS).format(name=name, company=COMPANY)
    f = random.choice(DM_OFFERS)
    c = random.choice(DM_CTAS)
    return f"{name}! 👋\n\n{o.split(', ', 1)[-1] if ', ' in o else o}\n\n{f}\n\n{c}\n\n- {COMPANY}"

def build_email(name, detail, region="Europe"):
    subject = random.choice(EMAIL_SUBJECTS).format(name=name, company=COMPANY)
    region_phrase = "across the United States" if region == "USA" else "across Europe"
    body = f"""{name} team,

We're {COMPANY}, martial arts and sportswear manufacturers based in Sialkot, Pakistan, producing for clubs and schools {region_phrase}.

We noticed your {detail} and would love to introduce what we do:

- Custom uniforms, gis, belts and protective gear with your club's own branding
- OEM / private-label manufacturing at factory-direct prices
- Small minimum order quantities designed for clubs, not just big distributors
- 3-4 weeks production and delivery {region_phrase}

If it's useful, we can send our catalog and wholesale price list, no commitment, just so you have us on file for when you need custom gear.

Best regards,
{COMPANY}
{EMAIL}
{PHONE}
"""
    return subject, body
