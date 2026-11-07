#!/usr/bin/env python3
"""Split the photo contact sheet into smaller batches so each can be
classified reliably (the 37-photo sheet in one image was too dense)."""
import os
from PIL import Image, ImageDraw

SRC = '/home/ubuntu/product_photos'
files = sorted(f for f in os.listdir(SRC) if f.lower().endswith(('.jpg', '.jpeg', '.png')))
COLS, TW, TH, PAD, LBL = 3, 330, 330, 10, 30
PER_BATCH = 9

for b in range(0, len(files), PER_BATCH):
    batch = files[b:b + PER_BATCH]
    rows = (len(batch) + COLS - 1) // COLS
    W = COLS * (TW + PAD) + PAD
    H = rows * (TH + LBL + PAD) + PAD
    sheet = Image.new('RGB', (W, H), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(batch):
        r, c = divmod(i, COLS)
        x = PAD + c * (TW + PAD)
        y = PAD + r * (TH + LBL + PAD)
        try:
            im = Image.open(os.path.join(SRC, f)).convert('RGB')
            im.thumbnail((TW, TH))
            sheet.paste(im, (x + (TW - im.width) // 2, y + (TH - im.height) // 2))
        except Exception:
            d.text((x + 5, y + 5), 'ERR', fill=(200, 0, 0))
        d.rectangle([x, y, x + TW, y + TH], outline=(150, 150, 150))
        num = b + i + 1
        d.text((x + 4, y + TH + 7), '#%d' % num, fill=(0, 0, 0))
    out = '/home/ubuntu/photos_batch_%d.jpg' % (b // PER_BATCH + 1)
    sheet.save(out, quality=90)
    print('%s -> %s' % (out, [b + i + 1 for i in range(len(batch))]))
