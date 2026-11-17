# Client Reply Templates — Price List Requests

## When to Use
Client asks: "Good evening, could you please send me the price lists?" or similar price list inquiry.

## Channel-Specific Templates

### Instagram DM (Primary — JPG + Link)
> Good evening! Here's our wholesale price list — JPG attached so it opens instantly in chat.
> 
> **HSN Warrior Apparels** — Martial Arts & Sportswear, manufactured in Sialkot
> - Custom branding (logo/colours) included from 30 pcs
> - Prices FOB Sialkot in EUR & USD
> - Door-to-door shipping, customs handled by us — no surprise fees
> 
> Full PDF also here: `[VERCEL_URL]`
> 
> What items does your club/team need? I'll send a mockup + exact quote today.

### Email / WhatsApp (If they prefer PDF)
> Good evening! Happy to send the full PDF — what's the best email?
> 
> (Our price list covers BJJ gis, rash guards, MMA shorts/tights, boxing gloves, shin guards, headgear, hoodies, belts — all custom-branded from 30 pcs, shipped door-to-door tax-free.)

### Short & Punchy (High-intent buyers)
> Evening! Price list attached (JPG) + PDF link below. All prices are club rates — custom branding included, 30 pcs MOQ, 4–6 week production, delivered to your door with zero customs hassle.
> 
> `[VERCEL_URL]`
> 
> Which categories are you sourcing? I'll prepare a tailored quote with mockups.

## Instagram-Specific Notes
- **Instagram DMs don't support PDF uploads** — JPG is the native format
- Always include the hosted PDF link as backup
- Deploy PDF to Vercel first: `vercel deploy --prod` from `/home/ubuntu/mibro-website-v3`
- Public URL pattern: `https://mibro-website-v3-<deployment>.vercel.app/price-list.pdf`
- For main domain (`hsnwarriorapparels.vercel.app`), deploy to that specific project

## Customization Points
- Replace `[VERCEL_URL]` with actual deployment URL
- Mention specific product categories if client's sport is known (BJJ, Muay Thai, Boxing, etc.)
- **For Instagram: analyze the handle/profile first** — see `references/instagram-profile-personalization.md` for signal extraction (handle parsing, bio signals, sport-specific SKU maps) and personalized template structure
- Keep sign-off: `— HSN Warrior Apparels` (company name only, no personal name)
- One question back to drive conversation: "What items does your club/team need?"

## Anti-Patterns to Avoid
- ❌ "I hope you're doing well" — generic opening
- ❌ "My name is Ghulam Hassan" — sender identity conflict with brand
- ❌ Full 12-SKU dump in one message — overwhelming
- ❌ No hook — why *this* club? Why now?
- ❌ Casual emojis (🙏) — keep professional
- ✅ One clear CTA: quantity question
- ✅ Specific value props: MOQ, branding included, tax-free shipping
- ✅ Brand identity: HSN Warrior Apparels, Sialkot, since 2011