#!/usr/bin/env python3
"""Crop the WhatsApp QR code out of the desktop screenshot."""
import sys
from PIL import Image

src = sys.argv[1] if len(sys.argv) > 1 else '/home/ubuntu/wa_desk_active.png'
dst = sys.argv[2] if len(sys.argv) > 2 else '/home/ubuntu/wa_qr_day15.png'
im = Image.open(src).convert('RGB')
W, H = im.size
print('screenshot size:', W, H)
# The WA tab content is the active tab region. Scan a grid for the largest
# high-contrast square block (the QR).
best = None
step = 20
for size in range(360, 140, -20):
    for y in range(0, H - size, step):
        for x in range(0, W - size, step):
            crop = im.crop((x, y, x + size, y + size)).convert('L')
            px = crop.load()
            dark = 0
            n = 0
            for yy in range(0, size, 4):
                for xx in range(0, size, 4):
                    n += 1
                    if px[xx, yy] < 110:
                        dark += 1
            if n and (dark / n) > 0.30:
                # verify a white quiet zone around it
                area = im.crop((max(0, x - 14), max(0, y - 14),
                                min(W, x + size + 14), min(H, y + size + 14))).convert('L')
                apx = area.load()
                aw, ah = area.size
                light = 0
                an = 0
                for yy in range(0, ah, 6):
                    for xx in range(0, aw, 6):
                        an += 1
                        if apx[xx, yy] > 170:
                            light += 1
                if an and (light / an) > 0.45:
                    best = (x, y, size)
                    break
        if best:
            break
    if best:
        break

if not best:
    print('QR NOT DETECTED - saving full screenshot instead')
    im.save(dst)
    sys.exit(1)

x, y, size = best
print('QR found at', best)
pad = 18
im.crop((max(0, x - pad), max(0, y - pad),
         min(W, x + size + pad), min(H, y + size + pad))).save(dst)
print('saved ->', dst)
