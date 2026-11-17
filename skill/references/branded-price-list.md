# Branded Price List Creation Workflow

## When to Use
Create a professional branded price list (PDF + JPG) from the user's source PDF for client delivery.

## Source Files
- User's price list PDF: `/home/ubuntu/.hermes/cache/documents/native-inputs/.../HSN_Price_List.pdf`
- Catalog PDF (specs only, no prices): `/home/ubuntu/HSN_Warrior_Apparels_Catalog.pdf`

## Workflow

### 1. Extract source content
```bash
pdftotext /path/to/HSN_Price_List.pdf -
```

### 2. Design branded HTML
Create `/tmp/hsn_price_list_branded.html` with:
- HSN Warrior Apparels branding (red/black theme, HW logo mark)
- Clean table: Product | EUR | USD | Material/Spec
- Sections: Fight Gloves, Headgear, Shin Guards, Grappling/No-Gi, Apparel & Teamwear
- Terms & Conditions (MOQ 30 pcs, branding included, 3-4 week production, door-to-door shipping)
- Contact footer with email, WhatsApp, Instagram, website
- CSS `@page` for print, `displayHeaderFooter: false` for clean PDF

### 3. Render to PDF via Chrome CDP
```python
# Connect to Chrome DevTools Protocol
# Page.printToPDF with displayHeaderFooter: False
# margins: 20mm all sides
```
Uses `/home/ubuntu/.hermes/tools/chromium-1208/chrome-linux/chrome` headless.

### 4. Render to JPG via Chrome CDP
```python
# Page.captureScreenshot with captureBeyondViewport: True, quality: 95
```
Produces full-page high-res JPG (1905×1890, ~360 KB).

### 5. Deploy PDF to Vercel for Instagram sharing
```bash
cp /tmp/HSN_Warrior_Apparels_Price_List_Branded.pdf /home/ubuntu/mibro-website-v3/public/price-list.pdf
cd /home/ubuntu/mibro-website-v3 && vercel deploy --prod
```
Public URL: `https://mibro-website-v3-<deployment>.vercel.app/price-list.pdf`

**Main domain (`hsnwarriorapparels.vercel.app`) is a SEPARATE Vercel project** — not in the current `paperdate25-hashs-projects` team. To deploy there:
- Option A: User runs `vercel --prod --scope=<team>` from `/home/ubuntu/mibro-website-v3` with access to that team
- Option B: Provide Vercel token for the team owning `hsnwarriorapparels.vercel.app`
- Preview URLs have Vercel auth protection; production URL or main domain needed for public access

## Instagram Delivery
- **Primary**: Send JPG in DM (works natively, no PDF support)
- **Backup**: Include hosted PDF link in message
- **Message template**: See `references/client-reply-templates.md`

## Professional Reply Templates

### Option 1 — Instagram DM with JPG
> Good evening! Here's our wholesale price list — JPG attached so it opens instantly in chat.
> 
> **HSN Warrior Apparels** — Martial Arts & Sportswear, manufactured in Sialkot
> - Custom branding (logo/colours) included from 30 pcs
> - Prices FOB Sialkot in EUR & USD
> - Door-to-door shipping, customs handled by us — no surprise fees
> 
> Full PDF also here: [Vercel URL]
> 
> What items does your club/team need? I'll send a mockup + exact quote today.

### Option 2 — If they prefer email/PDF
> Good evening! Happy to send the full PDF — what's the best email?
> 
> (Our price list covers BJJ gis, rash guards, MMA shorts/tights, boxing gloves, shin guards, headgear, hoodies, belts — all custom-branded from 30 pcs, shipped door-to-door tax-free.)

### Option 3 — Short & punchy
> Evening! Price list attached (JPG) + PDF link below. All prices are club rates — custom branding included, 30 pcs MOQ, 4–6 week production, delivered to your door with zero customs hassle.
> 
> [Vercel URL]
> 
> Which categories are you sourcing? I'll prepare a tailored quote with mockups.

## Pitfalls
- **Chrome CDP printToPDF requires Page.enable first** — attach to page target, enable Page domain, then print
- **displayHeaderFooter: False removes date/URL/page numbers** — essential for professional look
- **Vercel preview URLs have auth protection** — use production URL or deploy to main domain for public access
- **JPG is one long image** — client may need to zoom; consider multi-page JPG if needed
- **Source PDF has no prices** — catalog PDF is specs only; always use user's uploaded price list as source of truth

## Files Produced
- `/tmp/HSN_Warrior_Apparels_Price_List_Branded.pdf` — clean 3-page PDF
- `/tmp/HSN_Warrior_Apparels_Price_List.jpg` — full-page JPG for Instagram/WhatsApp
- Vercel deployment with public PDF URL