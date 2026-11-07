#!/usr/bin/env python3
"""Build the HSN Warrior Apparels logo and the go4WorldBusiness storefront
images, matching the live website's brand exactly.

Colours taken from the website CSS (styles.css):
  --red  #E01E2F   --red-hot #FF3040   --gold #C99A3C
  --ink  #0B0E14   --bone #F5F4F0      --paper #FFFFFF

The website logo mark is a red 32x11 chip with the wordmark
"HSN WARRIOR" over "Apparels", so the logo image reproduces that.
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = '/home/ubuntu/g4wb_assets'
os.makedirs(OUT, exist_ok=True)

RED = (224, 30, 47)
RED_HOT = (255, 48, 64)
GOLD = (201, 154, 60)
INK = (11, 14, 20)
BONE = (245, 244, 240)
PAPER = (255, 255, 255)


def font(size, bold=True):
    """Find a usable font. Prefer DejaVu (always present)."""
    cands = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
    ]
    for c in cands:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


def make_logo():
    W, H = 1000, 1000
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # red chip mark (matches .chip: red bar with a gold accent)
    d.rounded_rectangle([120, 300, 880, 420], radius=6, fill=RED)
    d.rounded_rectangle([120, 300, 250, 420], radius=6, fill=RED_HOT)
    # wordmark - three separate lines, no overlap
    f1 = font(120)
    f2 = font(120)
    f3 = font(88)
    t1 = 'HSN'
    t2 = 'WARRIOR'
    t3 = 'APPARELS'
    b1 = d.textbbox((0, 0), t1, font=f1)
    b2 = d.textbbox((0, 0), t2, font=f2)
    b3 = d.textbbox((0, 0), t3, font=f3)
    d.text(((W - (b1[2] - b1[0])) / 2 - b1[0], 470), t1, font=f1, fill=INK)
    d.text(((W - (b2[2] - b2[0])) / 2 - b2[0], 615), t2, font=f2, fill=INK)
    d.text(((W - (b3[2] - b3[0])) / 2 - b3[0], 760), t3, font=f3, fill=RED)
    # gold rule
    d.rectangle([120, 880, 880, 890], fill=GOLD)
    f4 = font(40)
    t4 = 'SIALKOT  PAKISTAN'
    b4 = d.textbbox((0, 0), t4, font=f4)
    d.text(((W - (b4[2] - b4[0])) / 2 - b4[0], 915), t4, font=f4, fill=(110, 114, 128))
    p = os.path.join(OUT, 'logo.png')
    im.save(p)
    print('logo ->', p, im.size)
    return p


def make_cover(title, sub, src=None):
    """A storefront cover: brand panel + optional real photo on the right."""
    W, H = 1200, 800
    im = Image.new('RGB', (W, H), BONE)
    d = ImageDraw.Draw(im)
    # left brand panel
    d.rectangle([0, 0, 520, H], fill=INK)
    d.rounded_rectangle([60, 120, 300, 168], radius=5, fill=RED)
    d.text((60, 210), 'HSN', font=font(92), fill=PAPER)
    d.text((60, 300), 'WARRIOR', font=font(64), fill=PAPER)
    d.text((60, 385), 'APPARELS', font=font(52), fill=RED)
    d.rectangle([60, 470, 460, 478], fill=GOLD)
    d.text((60, 505), 'Sialkot  Pakistan', font=font(34), fill=(166, 170, 179))
    # right: real photo or a solid brand block
    if src and os.path.exists(src):
        ph = Image.open(src).convert('RGB')
        ph.thumbnail((680, 800), Image.LANCZOS)
        im.paste(ph, (520 + (680 - ph.width) // 2, (H - ph.height) // 2))
    else:
        d.rectangle([520, 0, W, H], fill=RED)
        d.rectangle([520, 0, 560, H], fill=GOLD)
    return im


def make_cover_with_text(title, lines, src=None):
    im = make_cover(title, None, src)
    d = ImageDraw.Draw(im)
    f = font(52)
    y = 60
    for ln in lines:
        d.text((560, y), ln, font=f, fill=(255, 255, 255))
        y += 66
    return im


if __name__ == '__main__':
    make_logo()
    # storefront cover using a REAL product photo (gi on the floor, photo #2)
    cov = make_cover('BJJ Gi', None, '/home/ubuntu/product_photos/real_02.jpg')
    p = os.path.join(OUT, 'cover.png')
    cov.save(p)
    print('cover ->', p, cov.size)
    # factory photo for the office image
    fac = '/home/ubuntu/.hermes/cache/scratch/factory.jpg'
    if os.path.exists(fac):
        im = Image.open(fac).convert('RGB')
        im.thumbnail((1200, 900), Image.LANCZOS)
        p2 = os.path.join(OUT, 'factory.jpg')
        im.save(p2, quality=88)
        print('factory ->', p2, im.size)
