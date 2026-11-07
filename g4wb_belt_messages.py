"""g4wb belt inquiry messages - tailored per RFQ, then spam-QA'd.

Each message is written for that specific buyer's product, quantities,
payment terms and destination. Every message goes through the
spam-word-checker before it can be sent.
"""
import sys
sys.path.insert(0, '/home/ubuntu')
from spam_qa_followup import check

MESSAGES = {}

MESSAGES['taekwondo-belts'] = dict(
    subject='Taekwondo Belts - 3,500 pieces across 5 colours - our factory',
    body="""Dear Sir/Madam,

We are HSN Warrior Apparels, a martial arts and sportswear manufacturer and exporter based in Sialkot, Pakistan. We make taekwondo belts and doboks for clubs, federations and sports retailers worldwide.

Your requirement is 3,500 pieces across five colours - White 2,000, Green 1,000, Red 350, Black 50, Yellow 100. That is our standard production line, so we can price it directly:

- Rank belts in cotton or polyester, with a woven or printed rank bar
- Sizes from 160 cm to 210 cm, with a fixed overlap of 8 to 10 cm, or a length to your specification
- Your logo woven on the tip, or embroidered on a black label
- Stitched edges, not glued, so the belt holds its shape through repeated washing
- 3,500 pieces split across the five colours, delivered as five separate cartons

Our usual terms for an order of this size:
- 30 pieces per style and colour as the starting quantity, so your first run can test one colour before the full production
- 3 to 4 weeks production after artwork approval, then DHL, FedEx or UPS door to door in 4 to 6 working days
- CIF to your port in Malaysia, with shipping and customs handled on our side
- LC at sight, as your requirement states

Send us your logo file and the belt width you need, and we will reply with an exact price per colour and a sample mockup for one piece.

Best regards,
Ghulam Hassan
HSN Warrior Apparels
hsnwarriorapparel@gmail.com
+92 337 3336381""",
)

MESSAGES['martial-arts-belts-like-judo-belts'] = dict(
    subject='Judo Belts with your own logo - 100 pieces, CIF Portugal',
    body="""Dear Sir/Madam,

We are HSN Warrior Apparels, a martial arts and sportswear manufacturer and exporter based in Sialkot, Pakistan. We produce judo and martial arts belts for academies and sports retailers across Europe.

Your requirement is 100 judo belts with your own logo, in White/Yellow, Yellow, Yellow Orange and Orange, shipped CIF to a port in Portugal on LC terms. That is a standard production run for us:

- Rank belts in cotton or polyester, with a woven or printed rank bar
- Your logo woven on the belt tip or embroidered on a label
- Sizes from 160 cm to 210 cm, with an overlap of 8 to 10 cm, or a length to your specification
- Stitched edges, not glued
- 100 pieces split across the four colours, packed in separate cartons

Our terms for this run:
- 30 pieces per style and colour as the starting quantity
- 3 to 4 weeks production after artwork approval, then DHL, FedEx or UPS door to door in 4 to 6 working days
- CIF to your port in Portugal, with shipping and customs handled on our side
- LC at sight

Send us your logo file and the belt width you need, and we will reply with an exact quotation per colour and a sample mockup for one piece.

Best regards,
Ghulam Hassan
HSN Warrior Apparels
hsnwarriorapparel@gmail.com
+92 337 3336381""",
)

MESSAGES['boxing-accessories-like-hand-tie-gloves-head-guard'] = dict(
    subject='Boxing accessories - 500 to 1,000 pieces CIF Egypt',
    body="""Dear Sir/Madam,

We are HSN Warrior Apparels, a martial arts and sportswear manufacturer and exporter based in Sialkot, Pakistan. We produce boxing equipment and accessories for gyms, sports retailers and federations.

Your requirement is 500 to 1,000 pieces of boxing accessories - hand ties, gloves, head guards, mouth guards and caps - shipped CIF to Egypt on LC terms. Our production line covers every item on that list:

- Boxing gloves in vinyl or leather, 10 oz, 12 oz and 14 oz, with laced or hook-and-loop closure
- Head guards with a removable cheek guard and a padded forehead panel
- Mouth guards in a clear or coloured shell
- Boxing caps in cotton or poly-cotton, with an elastic band
- Hand ties in cotton or cotton-blend wrap, cut to length

Our terms for this run:
- 30 pieces per style as the starting quantity, so you can test one item before the full production
- 3 to 4 weeks production after artwork approval, then DHL, FedEx or UPS door to door in 4 to 6 working days
- CIF to your port in Egypt, with shipping and customs handled on our side
- LC at sight, as your requirement states

Send us the item mix you have in mind, your sizing and any branding you need applied, and we will reply with an exact quotation and a sample mockup for one piece.

Best regards,
Ghulam Hassan
HSN Warrior Apparels
hsnwarriorapparel@gmail.com
+92 337 3336381""",
)

MESSAGES['karate-black-master-belt'] = dict(
    subject='Karate and judo black master belts - 400 pieces - our factory',
    body="""Dear Sir/Madam,

We are HSN Warrior Apparels, a martial arts and sportswear manufacturer and exporter based in Sialkot, Pakistan. We make karate, judo and martial arts belts for academies, federations and sports retailers worldwide.

Your requirement is 400 pieces of black and brown karate and judo master belts with a logo, shipped CIF on TT terms. That is our standard production line:

- Master belts in cotton or polyester, with a woven or printed rank bar
- Black and brown, with your logo woven on the tip or embroidered on a label
- Sizes from 180 cm to 220 cm for adult master ranks, with an overlap of 8 to 10 cm, or a length to your specification
- Stitched edges, not glued, so the belt holds its shape through repeated washing
- 400 pieces delivered as one carton

Our terms for an order of this size:
- 30 pieces per style as the starting quantity, so your first run can test before the full production
- 3 to 4 weeks production after artwork approval, then DHL, FedEx or UPS door to door in 4 to 6 working days
- CIF to your destination, with shipping and customs handled on our side
- TT in advance as your requirement states

Send us your logo file and the belt width you need, and we will reply with an exact quotation and a sample mockup for one piece.

Best regards,
Ghulam Hassan
HSN Warrior Apparels
hsnwarriorapparel@gmail.com
+92 337 3336381""",
)

if __name__ == '__main__':
    bad = 0
    for key, m in MESSAGES.items():
        hits = check(m['subject'] + '\n' + m['body'], key)
        print('%-44s %s' % (key, 'OK' if not hits else 'FLAG'))
        for k, t in hits:
            print('      %-7s %r' % (k, t))
        if hits:
            bad += 1
    print()
    print('FAIL - %d message(s) flagged' % bad if bad else 'PASS - all messages clear the spam-word-checker')
    sys.exit(1 if bad else 0)
