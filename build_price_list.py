
"""Build a one-page price list PDF for a club/buyer enquiry."""
import json, sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

data = json.load(open('/home/ubuntu/g4wb_prices.json'))
out = sys.argv[1] if len(sys.argv) > 1 else '/home/ubuntu/HSN_Price_List.pdf'
title = sys.argv[2] if len(sys.argv) > 2 else 'Wholesale Price List'

styles = getSampleStyleSheet()
H = ParagraphStyle('H', parent=styles['Heading1'], fontSize=17, leading=21,
                   textColor=colors.HexColor('#111111'), spaceAfter=2)
SUB = ParagraphStyle('SUB', parent=styles['Normal'], fontSize=9, leading=12,
                     textColor=colors.HexColor('#555555'), spaceAfter=10)
CELL = ParagraphStyle('CELL', parent=styles['Normal'], fontSize=8.5, leading=11)
HEAD = ParagraphStyle('HEAD', parent=styles['Normal'], fontSize=8.5, leading=11,
                      textColor=colors.white)

doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=16*mm, rightMargin=16*mm,
                        topMargin=15*mm, bottomMargin=15*mm,
                        title='HSN Warrior Apparels Wholesale Price List',
                        author='HSN Warrior Apparels')

story = [Paragraph('HSN Warrior Apparels', H),
         Paragraph('Wholesale price list &nbsp;|&nbsp; Sialkot, Pakistan &nbsp;|&nbsp; '
                   'OEM / private label / club quantities &nbsp;|&nbsp; '
                   'hsnwarriorapparel@gmail.com &nbsp;|&nbsp; +92 337 3336381', SUB)]

rows = [[Paragraph('Product', HEAD), Paragraph('EUR', HEAD),
         Paragraph('USD', HEAD), Paragraph('Material / weight', HEAD)]]
NOTES = {
 'Jiu-Jitsu Gi (450g pearl weave)': '450 g pearl weave, pre-shrunk',
 'Shin Guards (cowhide)': 'Full-grain cowhide',
 'Boxing Gloves (cowhide)': 'Full-grain cowhide, laced',
 'Boxing Headgear (cowhide)': 'Full-grain cowhide, removable cheek pad',
 'Shin Guards (faux leather)': 'PU leather',
 'Boxing Gloves (faux leather)': 'PU leather, laced',
 'Boxing Headgear (faux leather)': 'PU leather',
 'Hoodie': 'Cotton / poly-cotton fleece',
 'MMA Tights': 'Spandex blend, flatlock seams',
 'MMA Shorts': 'Spandex blend, flatlock seams',
 'Rash Guard (short sleeve)': 'Polyester / spandex',
 'Jiu-Jitsu Belt': 'Cotton, rank bar woven or printed',
}
for name, p in data['prices'].items():
    rows.append([Paragraph(name, CELL),
                 Paragraph('%.2f' % p['eur'], CELL),
                 Paragraph('%.2f' % p['usd'], CELL),
                 Paragraph(NOTES.get(name, ''), CELL)])

t = Table(rows, colWidths=[78*mm, 22*mm, 22*mm, 55*mm], repeatRows=1)
t.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#111111')),
    ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#CCCCCC')),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F5F5F5')]),
    ('TOPPADDING', (0,0), (-1,-1), 5),
    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ('LEFTPADDING', (0,0), (-1,-1), 6),
]))
story.append(t)
story.append(Spacer(1, 8*mm))
story.append(Paragraph(
    '<b>Terms</b><br/>'
    'Minimum 30 pieces per style and colour. Your logo embroidered or woven in, '
    'in your colours. 3 to 4 weeks production after artwork approval. '
    'DHL, FedEx or UPS door to door. Customs and shipping handled on our side, so '
    'the price that lands at your door carries no added fee. '
    'Prices are FOB Sialkot for EUR and USD; a CIF quote is issued on request.', CELL))
story.append(Spacer(1, 4*mm))
story.append(Paragraph(
    'Full catalogue: <link href="https://hsnwarriorapparels.vercel.app/catalog.pdf">'
    'hsnwarriorapparels.vercel.app/catalog.pdf</link>', CELL))
doc.build(story)
print('wrote', out)
