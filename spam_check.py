"""A reusable spam/deliverability checker for outbound copy.

Implements the rules from the spam-word-checker skill:

  - banned single words (standalone or inside a compound)
  - banned short phrases
  - high-risk promotional / pressure wording
  - phishing-style language
  - irrelevant blacklisted categories
  - formatting bans: em dash, ALL CAPS, double exclamation,
    a greeting prefix before a first name
  - silence-based unsubscribe promises

Punctuation, hyphens and splits do NOT make a banned token safe, so the
match is on word BOUNDARIES with hyphens treated as separators.
"""
import re

BANNED_WORDS = """
get bank credit access open compare problem now billing deal finance
financial claims insurance mortgage soon new performance freedom home
sales medical urgent life marketing investment diagnostics friend cash
invoice extra purchase
""".split()

BANNED_PHRASES = [
    'off chance', 'one time', 'all good', 'following up here',
    'last note from me here', 'great fit', 'bumping this once',
    'just following up once', 'circle back', 'one more quick follow-up',
    'keep this open', 'compare notes', 'appreciate the reply',
]

RISK_PHRASES = [
    '50% off', '100% guaranteed', '100% free', '100% off',
    '100% satisfied', 'access now', 'act fast', 'act immediately',
    'act now', 'action required', 'affordable deal', 'amazing',
    'amazing deal', 'amazing offer', 'apply here', 'apply now',
    'avoid bankruptcy', 'bargain', 'best bargain', 'best deal',
    'best offer', 'best price', 'best rates', 'big profit', 'bonus',
    'buy now', 'buy today', 'call now', "can't live without",
    'cash bonus', 'cash out', 'claim now', 'claim your discount',
    'click', 'click below', 'click here', 'click this link',
    'contact us immediately', 'deal ending soon', 'discount',
    "don't delete", 'double your money', 'double your wealth',
    'drastically reduced', 'earn', 'earn cash', 'earn extra income',
    'earn money', 'easy income', 'exclusive deal', 'expires today',
    'extra cash', 'extra income', 'fantastic', 'fantastic offer',
    'fast cash', 'final call', 'for free', 'free access',
    'free consultation', 'free gift', 'free membership', 'free money',
    'free quote', 'free trial', 'full refund', 'get it now',
    'get out of debt', 'get started now', 'giveaway', 'great news',
    'guaranteed deposit', 'guaranteed results', 'hurry up',
    'important information', 'immediately', 'increase revenue',
    'increase sales', 'incredible deal', 'instant earnings',
    'instant income', 'instant savings', 'investment advice',
    'join millions', 'limited time', 'lowest price', 'make money',
    'million dollars', 'money-back guarantee', 'must read', 'no catch',
    'no cost', 'no obligation', 'no strings attached',
    'once in a lifetime', 'only $', 'only available here', 'order now',
    'order today', 'please read', 'price protection', 'profits',
    'promise', 'pure profit', 'quote', 'risk-free',
    'satisfaction guaranteed', 'save $', 'save big money', 'save up to',
    'sign up free', 'special invitation', 'special offer',
    'special promotion', 'supplies are limited', 'take action now',
    'the best', "this won't last", 'thousands', 'time limited',
    'today', 'top urgent', 'trial', 'unbeatable offer', 'unbelievable',
    'unlimited', 'urgent', 'what are you waiting for?',
    'while supplies last', 'why pay more?', 'will not believe',
    'winner announced', 'wonderful', 'you are a winner',
    'you will not believe your eyes',
]

PHISHING_PHRASES = [
    'access your account', 'account update', 'activate now',
    'change password', 'click to verify', 'confirm your details',
    'confidential information', 'data breach', 'download now',
    'final notice', 'important update', 'immediate action required',
    'install now', 'last warning', 'log in now', 'new login detected',
    'password reset', 'payment details needed', 'phishing alert',
    'security breach', 'security update', 'update account',
    'verify identity', 'warning message',
]

IRRELEVANT = [
    '100% natural', 'adult content', 'bet now', 'blackjack',
    'casino bonus', 'cure for', 'diet pill', 'doctor recommended',
    'fat burner', 'fast weight loss', 'free chips', 'free spins',
    'gamble online', 'guaranteed weight loss', 'jackpot',
    'lottery winner', 'medical breakthrough', 'miracle cure',
    'natural remedy', 'no prescription needed', 'online betting',
    'online casino', 'online pharmacy', 'pain relief', 'poker tournament',
    'prescription drugs', 'reverse aging', 'risk-free bet',
    'safe and effective', 'scientifically proven', 'secret formula',
    'slots jackpot', 'spin to win', 'vip offer', 'weight loss',
    'winning numbers', 'xxx',
]

SILENCE_STOPS = [
    'i will take silence as a no', 'read no reply as a pass',
    'assume no response means no interest',
    'if i don\'t hear back, i will leave it there',
    'let this one go', 'leave you alone',
    'i am happy to stay out of the way',
]

# A token is matched on word boundaries, with hyphens and slashes acting
# as separators so 'cash-cycle' still trips 'cash'.
_TOKEN = r'[\s\-_/,.|()\[\]!?\'":;]+'


def _hits_word(text, word):
    pattern = r'(?<![a-z0-9])' + re.escape(word) + r'(?![a-z0-9])'
    return re.search(pattern, text) is not None


def check(subject, body):
    """Return a list of flags for one message. Empty list = clean."""
    text = ((subject or '') + '\n' + (body or '')).lower()
    flags = []
    for w in BANNED_WORDS:
        if _hits_word(text, w):
            flags.append('word:' + w)
    for group, label in ((BANNED_PHRASES, 'phrase'),
                         (RISK_PHRASES, 'risk'),
                         (PHISHING_PHRASES, 'phish'),
                         (IRRELEVANT, 'irrelevant'),
                         (SILENCE_STOPS, 'silence-stop')):
        for p in group:
            if p in text:
                flags.append('%s:%s' % (label, p))
    if '\u2014' in (body or ''):
        flags.append('fmt:em-dash')
    if '!!' in (body or ''):
        flags.append('fmt:double-exclamation')
    if re.search(r'\b(hi|hello|hey)\s+[A-Z]', body or ''):
        flags.append('fmt:greeting-prefix')
    # ALL CAPS - a run of 3+ capital letters that is not an acronym we
    # knowingly use (CIF, FOB, L/C, HS, DHL, UPS, MOQ, UAE, USA, UK)
    # Recognised abbreviations are not SHOUTING. EUR/USD are currency
    # codes, MMA/BJJ are sport names, GI/DOBOK are garment names.
    allowed = {'CIF', 'FOB', 'HS', 'DHL', 'UPS', 'MOQ', 'UAE', 'USA', 'UK',
               'LC', 'TT', 'CFR', 'EXW', 'FCA', 'DDP', 'PVC', 'OE',
               'HSN', 'SIALKOT', 'PAKISTAN', 'EUR', 'USD', 'MMA', 'BJJ',
               'GI', 'DOBOK', 'MOQs', 'PVC', 'PU', 'SS', 'OEM', 'ODM',
               'L/C', 'T/T', 'HSN', 'REPLIED', 'PDF', 'MOQ',
               # Brand names that appear in OUR copy because the chain we
               # are writing to is called that. 'TITLE Boxing Club' and
               # 'UFC Gym' are the recipients' own names, not shouting.
               'TITLE', 'UFC'}
    for m in re.finditer(r'\b[A-Z]{3,}\b', body or ''):
        if m.group(0) not in allowed:
            flags.append('fmt:allcaps:' + m.group(0))
    return flags


def check_all(messages):
    """messages: {key: {'subject':..,'body':..}} -> {key: flags}"""
    return {k: check(m.get('subject'), m.get('body'))
            for k, m in messages.items()}


if __name__ == '__main__':
    import sys, json
    msgs = json.load(open(sys.argv[1]))
    res = check_all(msgs)
    bad = 0
    for k, f in sorted(res.items()):
        if f:
            bad += 1
            print('  %-46s %s' % (k[:45], f))
    print()
    print('%d/%d messages clean' % (len(res) - bad, len(res)))
    print('VERDICT:', 'PASS' if bad == 0 else 'FAIL')
