#!/usr/bin/env python3
"""Product listing data for go4WorldBusiness, built from the REAL product
photos in /home/ubuntu/product_photos and the official EUR price list.

Photo -> product mapping was done by classifying the contact sheets (only
real photos are used; no AI images). Photos that show the same product
family share the listing image.

go4WorldBusiness allows up to 15 products; we list 10, matching the price
list so the storefront and the price list agree.
"""
import json

# photo number -> product key (from the vision classification of the batches)
PHOTOS = {
    'gi':      [1, 2, 8, 10, 11, 12, 13, 14, 17, 18, 24, 26, 27, 35, 37],
    'rashguard': [4, 6, 7, 19, 29],
    'shorts':  [5, 9, 16, 22, 30, 31, 32, 33, 34, 36],
    'tee':     [15, 21, 23, 25, 28],
    'jacket':  [3, 20],
}
# product key -> the photo numbers used as listing images (max 3)
LISTING_PHOTOS = {
    'gi':        [1, 2, 8],
    'rashguard': [4, 19, 29],
    'shorts':    [5, 22, 30],
    'tee':       [21, 23, 25],
    'jacket':    [3, 20],
}


def photo_path(n):
    return '/home/ubuntu/product_photos/real_%02d.jpg' % n


def build():
    prices = json.load(open('/home/ubuntu/g4wb_prices.json'))
    P = prices['prices']

    def usd(key):
        return P[key]['usd']

    items = []

    items.append({
        'name': 'Custom BJJ Gi - 450g Pearl Weave',
        'grade': 'Competition',
        'min_price': usd('Jiu-Jitsu Gi (450g pearl weave)'),
        'max_price': usd('Jiu-Jitsu Gi (450g pearl weave)'),
        'unit': 'Piece',
        'incoterm': 'DDP',
        'moq': 30,
        'moq_unit': 'Pieces',
        'delivery_time': '25',
        'delivery_unit': 'Days',
        'pack': 'Poly bag with your logo label. Export carton 100 pcs per carton.',
        'capacity': '5000 pcs per month',
        'country': 'Pakistan',
        'sample': 'Buyer',
        'sample_cost': 'Supplier',
        'seller_code': 'HSN-GI-450',
        'standards': 'OEKO-TEX, REACH',
        'trademark': 'Buyer option available',
        'loading_port': 'Karachi, Pakistan',
        'usage': 'Brazilian Jiu-Jitsu academies, BJJ clubs, grappling schools, MMA gyms and martial arts schools that need competition-grade uniforms with their own logo.',
        'brand': 'Buyer / HSN Warrior Apparels',
        'model': 'HSN-GI-450-PW',
        'hs_code': '6209.20',
        'specs': [
            '450g pearl weave cotton-poly fabric',
            'Pre-shrunk, colour-fast, competition cut',
            'Reinforced stress points and bar-tacked seams',
            'Your logo embroidered or printed, your colours',
            'A0 to A5 sizes plus custom sizing',
        ],
        'advantages': [
            '30+ units per style, no container loads',
            'Logo included in every order',
            '3-4 weeks production, door-to-door courier in 4-6 days',
            'Tax-free shipping handled on our side',
        ],
        'photos': LISTING_PHOTOS['gi'],
        'desc': (
            'Custom Brazilian Jiu-Jitsu Gi - 450g Pearl Weave - Club Uniform for BJJ '
            'academies, grappling schools and MMA gyms.\n\n'
            'Competition-grade Brazilian Jiu-Jitsu gi in 450g pearl weave, made to order with '
            'your club logo and colours. 450g pearl weave is the standard for BJJ competition: '
            'light enough to move in, dense enough to hold its shape through years of hard grappling '
            'and washing. We pre-shrink the fabric so the fit your athletes order is the fit they get.\n\n'
            'Every order includes your own logo and colours, on the jacket back, the chest and the '
            'pants leg. Minimum order is 30 units per style, so a club can test sizing and stitching '
            'on real people before committing to a full group order. We build a digital mockup first '
            'so you approve the artwork before anything goes into production.\n\n'
            'Production takes 3-4 weeks from artwork approval. Shipping is by DHL, FedEx or UPS, '
            'door to door in 4-6 working days, and we handle shipping and customs so the total that '
            'lands at your door carries no added fees.'
        ),
    })

    items.append({
        'name': 'Custom Rash Guard - Short Sleeve',
        'grade': 'Competition',
        'min_price': usd('Rash Guard (short sleeve)'),
        'max_price': usd('Rash Guard (short sleeve)'),
        'unit': 'Piece',
        'incoterm': 'DDP',
        'moq': 30,
        'moq_unit': 'Pieces',
        'delivery_time': '20',
        'delivery_unit': 'Days',
        'pack': 'Poly bag with your logo label. Export carton 100 pcs per carton.',
        'capacity': '8000 pcs per month',
        'country': 'Pakistan',
        'sample': 'Buyer',
        'sample_cost': 'Supplier',
        'seller_code': 'HSN-RG-SS',
        'standards': 'OEKO-TEX, REACH',
        'trademark': 'Buyer option available',
        'loading_port': 'Karachi, Pakistan',
        'usage': 'BJJ academies, MMA gyms, grappling teams, wrestling clubs, no-gi BJJ and fitness clubs.',
        'brand': 'Buyer / HSN Warrior Apparels',
        'model': 'HSN-RG-SS',
        'hs_code': '6109.90',
        'specs': [
            '80-90 gsm stretch compression polyester',
            'Flatlock stitching, no chafing seams',
            'Silicone hem grip, stays in place',
            'Full sublimation or rubber logo print',
            'Your logo, colours and team name',
        ],
        'advantages': [
            '30+ units per style, no container loads',
            'Logo included in every order',
            '3-4 weeks production, door-to-door courier in 4-6 days',
            'Tax-free shipping handled on our side',
        ],
        'photos': LISTING_PHOTOS['rashguard'],
        'desc': (
            'Short-sleeve compression rash guard for BJJ, MMA and grappling teams. The fabric is a '
            'stretch polyester with flatlock seams so it stays comfortable through long grappling '
            'sessions and a full fight, and the silicone hem grip keeps it in place during takedowns.\n\n'
            'Printing options are full sublimation for photographic team graphics, or a clean rubber '
            'or embroidered logo for a more understated look. Your colours and team name go on every '
            'piece. Minimum order is 30 units per style, and we build a digital mockup first so you '
            'approve the artwork before production.\n\n'
            'Production takes 3-4 weeks from artwork approval. Shipping is by DHL, FedEx or UPS, '
            'door to door in 4-6 working days, and we handle shipping and customs so the total that '
            'lands at your door carries no added fees.'
        ),
    })

    items.append({
        'name': 'Custom MMA Grappling Shorts',
        'grade': 'Competition',
        'min_price': usd('MMA Shorts'),
        'max_price': usd('MMA Shorts'),
        'unit': 'Piece',
        'incoterm': 'DDP',
        'moq': 30,
        'moq_unit': 'Pieces',
        'delivery_time': '20',
        'delivery_unit': 'Days',
        'pack': 'Poly bag with your logo label. Export carton 100 pcs per carton.',
        'capacity': '10000 pcs per month',
        'country': 'Pakistan',
        'sample': 'Buyer',
        'sample_cost': 'Supplier',
        'seller_code': 'HSN-MMA-SH',
        'standards': 'OEKO-TEX, REACH',
        'trademark': 'Buyer option available',
        'loading_port': 'Karachi, Pakistan',
        'usage': 'MMA gyms, BJJ academies, grappling clubs, fightwear brands, boxing gyms and fitness studios.',
        'brand': 'Buyer / HSN Warrior Apparels',
        'model': 'HSN-MMA-SH',
        'hs_code': '6104.30',
        'specs': [
            'Lightweight ripstop or stretch woven fabric',
            '7-inch inseam on the fight cut, 9-inch on the training cut',
            'Elastic waistband with inner drawstring and silicone grip',
            'Flatlock seams, split-leg side seam for unrestricted movement',
            'Sublimation or rubber logo print, your colours',
        ],
        'advantages': [
            '30+ units per style, no container loads',
            'Logo included in every order',
            '3-4 weeks production, door-to-door courier in 4-6 days',
            'Tax-free shipping handled on our side',
        ],
        'photos': LISTING_PHOTOS['shorts'],
        'desc': (
            'MMA and grappling shorts in a lightweight ripstop or stretch woven, built for the way '
            'these are actually worn: rolling on the mat, kicking in a cage, and being washed after '
            'every session. The split-leg side seam and flatlock stitching give unrestricted movement '
            'with nothing rubbing.\n\n'
            'Two cuts are available: a 7-inch fight cut and a 9-inch training cut. The elastic '
            'waistband has an inner drawstring plus a silicone grip strip so the shorts stay up '
            'through a full session. Logo is sublimation or rubber print in your colours. Minimum '
            'order is 10 pieces per item, and we build a digital mockup first.\n\n'
            'Production takes 3-4 weeks from artwork approval. Shipping is by DHL, FedEx or UPS, '
            'door to door in 4-6 working days, and we handle shipping and customs so the total that '
            'lands at your door carries no added fees.'
        ),
    })

    items.append({
        'name': 'Custom MMA Tights Full Length',
        'grade': 'Competition',
        'min_price': usd('MMA Tights'),
        'max_price': usd('MMA Tights'),
        'unit': 'Piece',
        'incoterm': 'DDP',
        'moq': 30,
        'moq_unit': 'Pieces',
        'delivery_time': '20',
        'delivery_unit': 'Days',
        'pack': 'Poly bag with your logo label. Export carton 100 pcs per carton.',
        'capacity': '8000 pcs per month',
        'country': 'Pakistan',
        'sample': 'Buyer',
        'sample_cost': 'Supplier',
        'seller_code': 'HSN-MMA-TG',
        'standards': 'OEKO-TEX, REACH',
        'trademark': 'Buyer option available',
        'loading_port': 'Karachi, Pakistan',
        'usage': 'MMA teams, grappling academies, BJJ schools, wrestling clubs and combat sports clubs.',
        'brand': 'Buyer / HSN Warrior Apparels',
        'model': 'HSN-MMA-TG',
        'hs_code': '6104.30',
        'specs': [
            '230-260 gsm compression fabric with four-way stretch',
            'Flatlock seams throughout',
            'Ankle or full-length leg options',
            'Reinforced flatlock crotch for durability',
            'Sublimation or rubber logo print, your colours',
        ],
        'advantages': [
            '30+ units per style, no container loads',
            'Logo included in every order',
            '3-4 weeks production, door-to-door courier in 4-6 days',
            'Tax-free shipping handled on our side',
        ],
        'photos': [22, 30],
        'desc': (
            'Full-length MMA tights in a 230-260 gsm compression fabric with four-way stretch. Made '
            'for grappling and MMA teams that want a full kit matching, and for cold-weather training '
            'where a layer matters.\n\n'
            'The seams are flatlocked throughout and the crotch is reinforced with a flatlock gusset, '
            'which is where cheaper tights give out first. Logo is sublimation or rubber print in '
            'your colours. Minimum order is 30 units per style, and we build a digital mockup first '
            'so you approve the artwork before production.\n\n'
            'Production takes 3-4 weeks from artwork approval. Shipping is by DHL, FedEx or UPS, '
            'door to door in 4-6 working days, and we handle shipping and customs so the total that '
            'lands at your door carries no added fees.'
        ),
    })

    items.append({
        'name': 'Custom Jiu-Jitsu Competition Belt',
        'grade': 'Competition',
        'min_price': usd('Jiu-Jitsu Belt'),
        'max_price': usd('Jiu-Jitsu Belt'),
        'unit': 'Piece',
        'incoterm': 'DDP',
        'moq': 30,
        'moq_unit': 'Pieces',
        'delivery_time': '15',
        'delivery_unit': 'Days',
        'pack': 'Poly bag with your logo label. Export carton 200 pcs per carton.',
        'capacity': '20000 pcs per month',
        'country': 'Pakistan',
        'sample': 'Buyer',
        'sample_cost': 'Supplier',
        'seller_code': 'HSN-BELT',
        'standards': 'OEKO-TEX',
        'trademark': 'Buyer option available',
        'loading_port': 'Karachi, Pakistan',
        'usage': 'BJJ academies, karate clubs, judo clubs, jiu-jitsu schools and grappling academies.',
        'brand': 'Buyer / HSN Warrior Apparels',
        'model': 'HSN-BELT',
        'hs_code': '6209.90',
        'specs': [
            'Cotton webbing with multi-layer stitching',
            'Rank bar stitched at the exact competition width',
            'Black, blue, brown, purple, coral, green and red colour options',
            'Your club name embroidered on the bar',
            'IBJJF and IJF-compatible sizing',
        ],
        'advantages': [
            '30+ units per style, no container loads',
            'Logo included in every order',
            '3-4 weeks production, door-to-door courier in 4-6 days',
            'Tax-free shipping handled on our side',
        ],
        'photos': [5],
        'desc': (
            'Competition rank belts in cotton webbing with multi-layer stitching on the bar and the '
            'ends. Built to competition width so the bar sits correctly under the gi when you tie '
            'it, and to the right length for your athletes.\n\n'
            'All standard rank colours are available. Your club name is embroidered on the bar in '
            'white or gold thread. Minimum order is 30 units per style, and we send a photo proof of '
            'one belt before the full run.\n\n'
            'Production takes 3-4 weeks from artwork approval. Shipping is by DHL, FedEx or UPS, '
            'door to door in 4-6 working days, and we handle shipping and customs so the total that '
            'lands at your door carries no added fees.'
        ),
    })

    items.append({
        'name': 'Custom Boxing Gloves Cowhide',
        'grade': 'Professional',
        'min_price': usd('Boxing Gloves (cowhide)'),
        'max_price': usd('Boxing Gloves (cowhide)'),
        'unit': 'Pair',
        'incoterm': 'DDP',
        'moq': 30,
        'moq_unit': 'Pairs',
        'delivery_time': '25',
        'delivery_unit': 'Days',
        'pack': 'Individual poly bag with your logo label. Export carton 50 pairs per carton.',
        'capacity': '5000 pairs per month',
        'country': 'Pakistan',
        'sample': 'Buyer',
        'sample_cost': 'Supplier',
        'seller_code': 'HSN-BOX-GLV',
        'standards': 'REACH',
        'trademark': 'Buyer option available',
        'loading_port': 'Karachi, Pakistan',
        'usage': 'Boxing gyms, fight clubs, amateur and professional boxing teams, kickboxing clubs and MMA gyms.',
        'brand': 'Buyer / HSN Warrior Apparels',
        'model': 'HSN-BOX-GLV',
        'hs_code': '4016.10',
        'specs': [
            'Full-grain cowhide leather shell, hand stitched',
            'Multi-layer high-density foam padding',
            'Pre-curved hand with attached thumb',
            'Wide wrist closure with double D-ring',
            'Your club logo embroidered or printed on the wrist',
        ],
        'advantages': [
            '30+ units per style, no container loads',
            'Logo included in every order',
            '3-4 weeks production, door-to-door courier in 4-6 days',
            'Tax-free shipping handled on our side',
        ],
        'photos': [3],
        'desc': (
            'Professional boxing gloves in full-grain cowhide leather, hand stitched, with multi-layer '
            'high-density foam padding. Cowhide keeps its shape and grip through years of daily bag '
            'work where synthetic leather cracks and loses its shape.\n\n'
            'The hand is pre-curved and the thumb is attached for a closed-fist fit. The wrist closure '
            'is a wide strap with a double D-ring for a secure, adjustable fit. Your club logo goes on '
            'the wrist. Available in 10, 12, 14 and 16 ounce weights. Minimum order is 30 pairs, and '
            'we send a photo proof before the full run.\n\n'
            'Production takes 3-4 weeks from artwork approval. Shipping is by DHL, FedEx or UPS, '
            'door to door in 4-6 working days, and we handle shipping and customs so the total that '
            'lands at your door carries no added fees.'
        ),
    })

    items.append({
        'name': 'Custom Boxing Headgear Cowhide',
        'grade': 'Professional',
        'min_price': usd('Boxing Headgear (cowhide)'),
        'max_price': usd('Boxing Headgear (cowhide)'),
        'capacity': '3000 pieces per month',
        'unit': 'Piece',
        'incoterm': 'DDP',
        'moq': 30,
        'moq_unit': 'Pieces',
        'delivery_time': '25',
        'delivery_unit': 'Days',
        'pack': 'Individual poly bag with your logo label. Export carton 40 pcs per carton.',
        'country': 'Pakistan',
        'sample': 'Buyer',
        'sample_cost': 'Supplier',
        'seller_code': 'HSN-BOX-HEAD',
        'standards': 'REACH',
        'trademark': 'Buyer option available',
        'loading_port': 'Karachi, Pakistan',
        'usage': 'Boxing gyms, amateur fight clubs, kickboxing schools and MMA gyms running sparring sessions.',
        'brand': 'Buyer / HSN Warrior Apparels',
        'model': 'HSN-BOX-HEAD',
        'hs_code': '6506.10',
        'specs': [
            'Full-grain cowhide leather shell',
            'Multi-layer foam cheek and forehead padding',
            'Adjustable top and rear strap with buckle',
            'Removable face bar for sparring',
            'Your club logo embroidered on the forehead',
        ],
        'advantages': [
            '30+ units per style, no container loads',
            'Logo included in every order',
            '3-4 weeks production, door-to-door courier in 4-6 days',
            'Tax-free shipping handled on our side',
        ],
        'photos': [20],
        'desc': (
            'Full-face boxing headgear in full-grain cowhide leather, built for regular sparring '
            'rather than occasional use. The cheek and forehead padding is multi-layer foam, and '
            'the removable face bar lets you set the protection level for your session.\n\n'
            'Top and rear straps are adjustable with a buckle so the fit can be tightened per boxer, '
            'and the interior liner is replaceable. Your club logo is embroidered on the forehead. '
            'Minimum order is 30 units per style, and we send a photo proof before the full run.\n\n'
            'Production takes 3-4 weeks from artwork approval. Shipping is by DHL, FedEx or UPS, '
            'door to door in 4-6 working days, and we handle shipping and customs so the total that '
            'lands at your door carries no added fees.'
        ),
    })

    items.append({
        'name': 'Custom Shin Guards Cowhide',
        'grade': 'Professional',
        'min_price': usd('Shin Guards (cowhide)'),
        'max_price': usd('Shin Guards (cowhide)'),
        'unit': 'Pair',
        'incoterm': 'DDP',
        'moq': 30,
        'moq_unit': 'Pairs',
        'delivery_time': '25',
        'delivery_unit': 'Days',
        'pack': 'Individual poly bag with your logo label. Export carton 50 pairs per carton.',
        'capacity': '5000 pairs per month',
        'country': 'Pakistan',
        'sample': 'Buyer',
        'sample_cost': 'Supplier',
        'seller_code': 'HSN-SHIN-CW',
        'standards': 'REACH',
        'trademark': 'Buyer option available',
        'loading_port': 'Karachi, Pakistan',
        'usage': 'Boxing gyms, kickboxing clubs, MMA gyms and martial arts schools running contact and sparring training.',
        'brand': 'Buyer / HSN Warrior Apparels',
        'model': 'HSN-SHIN-CW',
        'hs_code': '4205.00',
        'specs': [
            'Full-grain cowhide leather shell',
            'Dual-density foam over instep and shin',
            'Ankle strap with hook-and-loop closure',
            'Contoured calf section for a close fit',
            'Your club logo printed on the strap',
        ],
        'advantages': [
            '30+ units per style, no container loads',
            'Logo included in every order',
            '3-4 weeks production, door-to-door courier in 4-6 days',
            'Tax-free shipping handled on our side',
        ],
        'photos': [3],
        'desc': (
            'Boxing and kickboxing shin guards in full-grain cowhide leather with dual-density foam '
            'over the instep and shin, where kicks actually land. The contoured calf section gives a '
            'close fit so the guard does not rotate on impact.\n\n'
            'The ankle strap uses hook-and-loop closure so it can be adjusted to fit each fighter. '
            'Your club logo is printed on the strap. Available in small, medium and large, and also in '
            'faux leather at a lower price point. Minimum order is 30 pairs, and we send a photo proof '
            'before the full run.\n\n'
            'Production takes 3-4 weeks from artwork approval. Shipping is by DHL, FedEx or UPS, '
            'door to door in 4-6 working days, and we handle shipping and customs so the total that '
            'lands at your door carries no added fees.'
        ),
    })

    items.append({
        'name': 'Custom Team Hoodie Fleece',
        'grade': 'Premium',
        'min_price': usd('Hoodie'),
        'max_price': usd('Hoodie'),
        'unit': 'Piece',
        'incoterm': 'DDP',
        'moq': 30,
        'moq_unit': 'Pieces',
        'delivery_time': '25',
        'delivery_unit': 'Days',
        'pack': 'Poly bag with your logo label. Export carton 50 pcs per carton.',
        'capacity': '6000 pcs per month',
        'country': 'Pakistan',
        'sample': 'Buyer',
        'sample_cost': 'Supplier',
        'seller_code': 'HSN-HOOD',
        'standards': 'OEKO-TEX',
        'trademark': 'Buyer option available',
        'loading_port': 'Karachi, Pakistan',
        'usage': 'Martial arts schools, boxing clubs, MMA gyms, fightwear brands and sportswear resellers.',
        'brand': 'Buyer / HSN Warrior Apparels',
        'model': 'HSN-HOOD',
        'hs_code': '6110.20',
        'specs': [
            '280 gsm brushed cotton-poly fleece',
            'Double-layer hood with flat drawstrings',
            'Ribbed cuffs and hem with elastane',
            'Kangaroo pocket',
            'Screen print, embroidery or rubber print, your colours',
        ],
        'advantages': [
            '30+ units per style, no container loads',
            'Logo included in every order',
            '3-4 weeks production, door-to-door courier in 4-6 days',
            'Tax-free shipping handled on our side',
        ],
        'photos': [3, 20],
        'desc': (
            'Brushed cotton-poly fleece hoodies for club and team wear, cut for people who train '
            'and then wear the same hoodie out of the gym. 280 gsm fleece holds its shape through '
            'repeated washing, and the double-layer hood keeps its shape without a drawstring tip '
            'breaking through.\n\n'
            'Branding options are screen print, embroidery or rubber print, in your colours, on the '
            'chest, back or sleeve. Minimum order is 30 units per style, and we build a digital '
            'mockup first so you approve the artwork before production.\n\n'
            'Production takes 3-4 weeks from artwork approval. Shipping is by DHL, FedEx or UPS, '
            'door to door in 4-6 working days, and we handle shipping and customs so the total that '
            'lands at your door carries no added fees.'
        ),
    })

    items.append({
        'name': 'Custom Team Wear T-Shirt',
        'grade': 'Premium',
        'min_price': usd('Rash Guard (short sleeve)'),
        'max_price': usd('Rash Guard (short sleeve)'),
        'unit': 'Piece',
        'incoterm': 'DDP',
        'moq': 30,
        'moq_unit': 'Pieces',
        'delivery_time': '20',
        'delivery_unit': 'Days',
        'pack': 'Poly bag with your logo label. Export carton 100 pcs per carton.',
        'capacity': '10000 pcs per month',
        'country': 'Pakistan',
        'sample': 'Buyer',
        'sample_cost': 'Supplier',
        'seller_code': 'HSN-TSH',
        'standards': 'OEKO-TEX',
        'trademark': 'Buyer option available',
        'loading_port': 'Karachi, Pakistan',
        'usage': 'Martial arts schools, boxing clubs, MMA gyms, fightwear brands, team uniforms and event staff wear.',
        'brand': 'Buyer / HSN Warrior Apparels',
        'model': 'HSN-TSH',
        'hs_code': '6109.10',
        'specs': [
            '180 gsm ringside cotton, combed and bio-washed',
            'Shoulder-to-shoulder taping for shape retention',
            'Twin-needle hems and collar',
            'Screen print, DTF, embroidery or rubber print',
            'Full colour printing in your brand palette',
        ],
        'advantages': [
            '30+ units per style, no container loads',
            'Logo included in every order',
            '3-4 weeks production, door-to-door courier in 4-6 days',
            'Tax-free shipping handled on our side',
        ],
        'photos': LISTING_PHOTOS['tee'],
        'desc': (
            'Ringside cotton team-wear t-shirts for clubs, gyms and event teams. 180 gsm combed and '
            'bio-washed cotton with shoulder-to-shoulder taping, so the shape survives being washed '
            'after every session instead of hanging on a hook and stretching out.\n\n'
            'Printing options are screen print, DTF for full-colour photographic graphics, '
            'embroidery, or rubber print for a heavier feel. We can print your full team kit in one '
            'run so everything matches. Minimum order is 30 units per style, and we build a digital '
            'mockup first.\n\n'
            'Production takes 3-4 weeks from artwork approval. Shipping is by DHL, FedEx or UPS, '
            'door to door in 4-6 working days, and we handle shipping and customs so the total that '
            'lands at your door carries no added fees.'
        ),
    })

    return items


if __name__ == '__main__':
    items = build()
    print('listings:', len(items))
    for i, it in enumerate(items, 1):
        print('%2d. %-58s min$%-6s max$%-6s photos=%s' % (
            i, it['name'][:58], it['min_price'], it['max_price'], it['photos']))
