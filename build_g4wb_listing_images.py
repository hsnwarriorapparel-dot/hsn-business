#!/usr/bin/env python3
"""Build go4WorldBusiness listing images.

WHY THIS EXISTS (2026-11-07): every photo in /home/ubuntu/product_photos
carries ANOTHER CLIENT's brand on the garment (GRACIE BARRA, PITBULL, FIGHT
CLUB, FERAL GEAR, EQUIPE, HURRICANE, SEVERE, REBELS, U&U, MUALA). The
catalog PDF images are no better (U&U, MUALA, CAPITAL). Listing those on our
own storefront would be passing another company's trademark off as our own.

So each listing image is COMPOSED:
  - our own logo (rebuilt from the live website brand colours)
  - a REAL factory / production photo from our own website assets
    (sewing-line.jpg is our own unit; gi-fabric / gym-team / karate-kids /
    judo-throw / mma-ground / hero-grappling are unbranded per the check)
  - the product name and spec, typeset in our brand style
No third-party garment is shown.

Website brand colours (styles.css):
  --red #E01E2F  --red-hot #FF3040  --gold #C99A3C
  --ink #0B0E14  --bone #F5F4F0     --paper #FFFFFF
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = '/home/ubuntu/g4wb_assets/listings'
os.makedirs(OUT, exist_ok=True)
SITE = 'https://hsnwarriorapparels.vercel.app/assets/img/'

RED = (224, 30, 47)
RED_HOT = (255, 48, 64)
GOLD = (201, 154, 60)
INK = (11, 14, 20)
BONE = (245, 244, 240)
PAPER = (255, 255, 255)
SOFT = (166, 170, 179)


def font(size, bold=True):
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


def local_photo(name):
    """Prefer an already-downloaded copy, else fetch it."""
    p = '/home/ubuntu/.hermes/cache/scratch/site_%s' % name
    if os.path.exists(p) and os.path.getsize(p) > 2000:
        return p
    return None


def make_listing_image(key, title, specs, photo_path, price_usd):
    W, H = 1000, 1000
    im = Image.new('RGB', (W, H), BONE)
    d = ImageDraw.Draw(im)

    # top brand bar
    d.rectangle([0, 0, W, 96], fill=INK)
    d.rounded_rectangle([48, 34, 232, 62], radius=4, fill=RED)
    d.text((258, 24), 'HSN WARRIOR', font=font(34), fill=PAPER)
    d.text((560, 30), 'APPARELS', font=font(30), fill=RED)

    # photo panel
    px0, py0, px1, py1 = 0, 96, W, 660
    if photo_path and os.path.exists(photo_path):
        try:
            ph = Image.open(photo_path).convert('RGB')
            # cover-crop to the panel
            sw, sh = px1 - px0, py1 - py0
            scale = max(sw / ph.width, sh / ph.height)
            ph = ph.resize((int(ph.width * scale) + 1, int(ph.height * scale) + 1), Image.LANCZOS)
            left = (ph.width - sw) // 2
            top = (ph.height - sh) // 2
            ph = ph.crop((left, top, left + sw, top + sh))
            im.paste(ph, (px0, py0))
            # subtle darkening so overlaid text stays readable
            ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            od = ImageDraw.Draw(ov)
            od.rectangle([0, py1 - 190, W, py1], fill=(11, 14, 20, 200))
            im = Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB')
            d = ImageDraw.Draw(im)
        except Exception:
            d.rectangle([px0, py0, px1, py1], fill=(30, 34, 42))
    else:
        d.rectangle([px0, py0, px1, py1], fill=(30, 34, 42))

    # product title over the photo bottom
    f_title = font(52)
    lines = wrap(d, title, f_title, W - 120)
    y = py1 - 60 - len(lines) * 58
    for ln in lines:
        d.text((60, y), ln, font=f_title, fill=PAPER)
        y += 58

    # spec block on the bone background
    y = 700
    f_spec = font(34)
    for s in specs:
        d.rectangle([60, y + 12, 76, y + 28], fill=RED)
        d.text((96, y), s, font=f_spec, fill=INK)
        y += 52

    # gold rule + price + footer
    d.rectangle([60, 936, 940, 944], fill=GOLD)
    f_price = font(40)
    d.text((60, 952), 'Factory price  USD %.2f' % price_usd, font=f_price, fill=RED)
    f_foot = font(26)
    d.text((940 - d.textbbox((0, 0), 'Sialkot  Pakistan', font=f_foot)[2], 960),
           'Sialkot  Pakistan', font=f_foot, fill=SOFT)

    p = os.path.join(OUT, '%s.png' % key)
    im.save(p, quality=90)
    print('  %-18s -> %s' % (key, p))
    return p


def wrap(draw, text, f, maxw):
    words = text.split()
    lines, cur = [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if draw.textbbox((0, 0), t, font=f)[2] <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines[:3]


# key -> (title, specs, website photo, price key)
ITEMS = {
    'gi': ('Custom Brazilian Jiu-Jitsu Gi - 450g Pearl Weave',
           ['450g pearl weave, pre-shrunk, competition cut',
            'Your logo and colours, embroidered or printed',
            'A0-A5 plus custom sizing'],
           'hero-grappling.jpg', 'Jiu-Jitsu Gi (450g pearl weave)'),
    'rashguard': ('Custom Rash Guard - Compression Short Sleeve',
                  ['80-90 gsm stretch polyester, flatlock seams',
                   'Full sublimation or rubber logo print',
                   'BJJ / MMA / no-gi grappling'],
                  'mma-ground.jpg', 'Rash Guard (short sleeve)'),
    'shorts': ('Custom MMA and Grappling Shorts',
               ['Lightweight ripstop or stretch woven',
                '7-inch fight cut or 9-inch training cut',
                'Silicone waistband grip'],
               'mma-ground.jpg', 'MMA Shorts'),
    'hoodie': ('Custom Team Hoodie - Brushed Cotton Fleece',
               ['280 gsm brushed cotton-poly fleece',
                'Double-layer hood, ribbed cuffs and hem',
                'Screen print, embroidery or rubber print'],
               'gym-team.jpg', 'Hoodie'),
    'tee': ('Custom Team Wear T-Shirt - Ringside Cotton',
            ['180 gsm combed bio-washed cotton',
             'Full colour printing in your palette',
             'Shoulder-to-shoulder taping'],
            'karate-kids.jpg', 'Rash Guard (short sleeve)'),
    'factory': ('In-House Manufacturing - Sialkot Industrial Estate',
                ['Cutting, stitching, embroidery and finishing',
                 'Your brand: woven labels, heat transfers, packaging',
                 '30+ units minimum per style'],
                'sewing-line.jpg', None),
}

if __name__ == '__main__':
    import json
    prices = json.load(open('/home/ubuntu/g4wb_prices.json'))['prices']
    for key, (title, specs, photo, pkey) in ITEMS.items():
        price = prices[pkey]['usd'] if pkey else 0.0
        make_listing_image(key, title, specs, local_photo(photo), price)
    print('done ->', OUT)
