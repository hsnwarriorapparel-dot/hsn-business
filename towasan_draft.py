"""DRAFT reply for TOWASAN Karate Schulen (L3372, Munich) - WhatsApp.

Their message (2026-11-07):
  "What kind of class are you proposing, and what would your role be? Please
   share a short outline so our team can review it."

WHY THIS IS THE RIGHT SHAPE (playbook):
  - They asked two questions. Answer BOTH, briefly.
  - They asked for a SHORT OUTLINE -> give a short outline, not a catalogue.
  - They want to REVIEW it internally -> make it easy to forward.
  - One question back (the smallest next step).
  - Honest about our role: we are the MANUFACTURER, not a coach. Their
    question "what would your role be" is a fair check - say exactly that.

Their facts (verified from towasan.de):
  - TOWASAN Karate Schulen, Kinderkarate ab 3 + Kickboxen, Muenchen
  - Programmes: Lil Dragon 3-5, Kinder Karate 6-8, Jugend Karate 9-13,
    Erwachsenen Karate 14+, Kickboxen + Kickboxen Morningclass
  - Locations in/around Munich: Berg am Laim, Gruenwald, Markt Schwaben, Schwabing
  - Their kickboxers need: gloves, shin guards, headgear, mouthguards, shorts
  - Their karate kids need: dobok/gi, belts, gloves (sparring), sparring pads

Copy rules applied (spam-word-checker + playbook):
  - no banned words, no em dash, no greeting prefix, no fake urgency
  - no "free sample", no unverified claims
  - company-name sign-off only
  - concrete products + real prices + one next step
"""
import sys
sys.path.insert(0, '/home/ubuntu')

# The EUR price list (source of truth in the skill).
PRICES = {
    'Gi (450g pearl weave)': 'EUR 29.60',
    'Rash Guard': 'EUR 9.50',
    'MMA Shorts': 'EUR 9.90',
    'MMA Tights': 'EUR 12.50',
    'Belt': 'EUR 3',
    'Boxing Gloves (cowhide)': 'EUR 25.50',
    'Shin Guards (cowhide)': 'EUR 28.50',
    'Headgear (cowhide)': 'EUR 24',
    'Hoodie': 'EUR 14.50',
}

DRAFT = """TOWASAN team,

Short answer: we do not run classes. We are the manufacturer. Our role is to make the uniform, gloves and protection your teams train in, with your own logo on every piece.

A short outline for your review:

What we would make for you
- Karate uniform (dobok) for Lil Dragon, Kinder, Jugend and Erwachsene, in your colours with your logo and the TOWASAN name on the back
- Rank belts to match your grade structure
- Kickboxing gear: gloves, shin guards, headgear, and shorts for the Morningclass
- Sparring gloves and pads for the kids programmes, so the Lil Dragon and Kinder groups have something safe to work with
- Walkout wear: hoodie or team shirt for the 5 locations

Factory prices
- Karate uniform, 450g pearl weave: EUR 29.60
- Rank belt: EUR 3
- Boxing or kickboxing gloves, cowhide: EUR 25.50
- Shin guards, cowhide: EUR 28.50
- Headgear, cowhide: EUR 24
- Hoodie: EUR 14.50

Every piece includes your logo and colours, minimum is 30 units per style, production is 3 to 4 weeks, and we ship door to door by DHL, FedEx or UPS with customs handled on our side, so no handling fee is added on arrival.

What we would need from you
- Your logo files (vector if you have them) and your colours
- Which programmes you want to kit out first, and roughly how many students per group
- One photo of your current uniform would help us match the cut

Which programme would you want to see a mockup for first?

Best regards,
HSN Warrior Apparels
hsnwarriorapparel@gmail.com
+92 337 3336381"""


def main():
    print(DRAFT)
    print()
    print('=' * 60)
    print('chars:', len(DRAFT))
    # quick banned-token self check
    from spam_qa_followup import check
    hits = check(DRAFT, 'towasan-draft')
    if hits:
        print('SPAM-CHECK FLAGS:')
        for k, t in hits:
            print('  %-7s %r' % (k, t))
    else:
        print('SPAM-CHECK: PASS')


if __name__ == '__main__':
    main()
