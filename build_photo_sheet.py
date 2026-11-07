#!/usr/bin/env python3
"""Build a numbered contact sheet of the real product photos so the USER can
pick which photo is which product (the agent cannot reliably classify
product types from images).

Rule from the skill: only REAL photos are used client-facing, and the agent
does not guess which photo shows which product. Deliver via MEDIA and let the
user pick numbers.
"""
import os
from PIL import Image, ImageDraw

SRC = '/home/ubuntu/product_photos'
OUT = '/home/ubuntu/product_photos_sheet.jpg'
files = sorted(f for f in os.listdir(SRC) if f.lower().endswith(('.jpg', '.jpeg', '.png')))
COLS, TW, TH, PAD, LBL = 5, 260, 260, 8, 28
rows = (len(files) + COLS - 1) // COLS
W = COLS * (TW + PAD) + PAD
H = rows * (TH + LBL + PAD) + PAD
sheet = Image.new('RGB', (W, H), (250, 250, 250))
d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    r, c = divmod(i, COLS)
    x = PAD + c * (TW + PAD)
    y = PAD + r * (TH + LBL + PAD)
    try:
        im = Image.open(os.path.join(SRC, f)).convert('RGB')
        im.thumbnail((TW, TH))
        sheet.paste(im, (x + (TW - im.width) // 2, y + (TH - im.height) // 2))
    except Exception as e:
        d.text((x + 5, y + 5), 'ERR', fill=(200, 0, 0))
    d.rectangle([x, y, x + TW, y + TH], outline=(180, 180, 180))
    d.text((x + 4, y + TH + 6), '#%d  %s' % (i + 1, f), fill=(20, 20, 20))
sheet.save(OUT, quality=88)
print('saved', OUT, sheet.size, 'photos:', len(files))
for i, f in enumerate(files):
    print('  #%d = %s' % (i + 1, f))
