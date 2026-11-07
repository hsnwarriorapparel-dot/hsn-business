#!/usr/bin/env python3
"""Spam-word-checker QA for the follow-up copy (and the first-touch template).

Reads the banned lists straight out of the spam-word-checker SKILL.md so the
check cannot drift from the rules. Exit code 1 = a banned token found.
"""
import re, sys, os

SKILL = '/home/ubuntu/.hermes/skills/spam-word-checker/SKILL.md'
sys.path.insert(0, '/home/ubuntu')


def load_banned():
    text = open(SKILL, encoding='utf-8').read()
    words, phrases = set(), set()

    # "Banned Single Words" section
    m = re.search(r'## Banned Single Words(.*?)(?=\n## )', text, re.S)
    if m:
        words |= set(re.findall(r'`([^`]+)`', m.group(1)))

    # "Banned Short Phrases"
    m = re.search(r'## Banned Short Phrases(.*?)(?=\n## )', text, re.S)
    if m:
        phrases |= set(re.findall(r'`([^`]+)`', m.group(1)))

    # High-risk + phishing + irrelevant sections: treat every backticked
    # phrase as banned, but split multi-word entries on ' - ' annotations.
    for header in ('High-Risk Promotional', 'Phishing-Style', 'Irrelevant Blacklisted'):
        m = re.search(r'## %s.*?(?=\n## |\Z)' % header, text, re.S)
        if m:
            for phrase in re.findall(r'`([^`]+)`', m.group(0)):
                phrase = phrase.split(' - ')[0].strip().lower()
                if not phrase:
                    continue
                if ' ' in phrase:
                    phrases.add(phrase)
                else:
                    words.add(phrase)
    return words, phrases


def check(text, label):
    words, phrases = load_banned()
    low = text.lower()
    hits = []
    for w in sorted(words):
        if not w:
            continue
        # word-boundary match, but also catch compounds like 'cash-cycle'
        if re.search(r'(?<![a-z])' + re.escape(w.lower()) + r'(?![a-z])', low):
            hits.append(('WORD', w))
    for p in sorted(phrases):
        if p and p in low:
            hits.append(('PHRASE', p))
    # formatting / style bans
    if '\u2014' in text:
        hits.append(('STYLE', 'em dash'))
    if re.search(r'\b(Hi|Hello|Hey)\s+', text):
        hits.append(('STYLE', 'greeting prefix'))
    if re.search(r'!{2,}', text):
        hits.append(('STYLE', 'multiple exclamation marks'))
    # ALL CAPS is only a problem for OUR copy. A brand's own name is allowed
    # to be capitalised ("TITLE Boxing Club", "UFC Gym", "HSN Warrior").
    _strip = text
    for _brand in ('HSN', 'EUR', 'USD', 'USA', 'MMA', 'BJJ', 'TITLE', 'UFC', 'GI',
                   'MOQ', 'DM', 'IG', 'WA', 'PDF', 'FAQ', 'DHL', 'UPS', 'XL',
                   'DOBOK', 'MOCKUP', 'OEM', 'MOQ', 'SIALKOT', 'MUNICH',
                   'TOWASAN', 'GRACIE', 'TITLE'):
        _strip = re.sub(r'\b' + _brand + r'\b', '', _strip)
    if re.search(r'\b[A-Z]{4,}\b', _strip):
        hits.append(('STYLE', 'ALL CAPS'))
    # silence-based stop promise
    if re.search(r'(silence.{0,30}(no|stop)|no response.{0,20}means|take silence|leave you alone|assume no)', low):
        hits.append(('RULE', 'silence-based stop promise'))
    return hits


if __name__ == '__main__':
    from templates import build_email
    import day23_followup as fu

    subjects_bodies = []
    # first-touch template (already live, but QA it too)
    for region in ('Europe', 'USA'):
        s, b = build_email('Test Gym', 'boxing gym', region=region)
        subjects_bodies.append(('first-touch[%s]' % region, s + '\n' + b))
    # follow-up angles
    for ang in fu.ANGLES:
        s, b = fu.build_followup({'name': 'Test Gym', 'country': 'Ireland'}, ang)
        subjects_bodies.append(('followup[%s]' % ang['key'], s + '\n' + b))

    bad = 0
    for label, txt in subjects_bodies:
        hits = check(txt, label)
        status = 'OK' if not hits else 'FLAG'
        if hits:
            bad += 1
        print('%-24s %s' % (label, status))
        for kind, tok in hits:
            print('      %-7s %r' % (kind, tok))
    print()
    print('FAIL' if bad else 'PASS - all copy clears the spam-word-checker')
    sys.exit(1 if bad else 0)
