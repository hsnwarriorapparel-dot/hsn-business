# Instagram Profile Analysis for Personalized Outreach

## When to Use
Before sending a cold IG DM or reply to a new lead. Turn the handle + visible profile signals into a sport-specific, club-aware message that proves you looked at their page.

## Signal Extraction Rules

### Handle Parsing
| Handle Segment | Likely Meaning | Action |
|---|---|---
| `bjj`, `jiujitsu`, `jiu-jitsu`, `gracie` | Brazilian Jiu-Jitsu | Lead with gis, rash guards, belts, kids' gis |
| `muaythai`, `muay`, `thai`, `nakmuay` | Muay Thai | Lead with gloves, shin guards, shorts |
| `boxing`, `boxeo`, `pugilism` | Boxing | Lead with gloves, headgear, hand wraps |
| `judo`, `jujutsu` | Judo | Lead with judogi, belts |
| `karate`, `shotokan`, `kyokushin` | Karate | Lead with karategi, hand/foot gear |
| `mma`, `mixedmartialarts`, `cage` | MMA | Lead with MMA shorts, rash guards, gloves |
| `academy`, `academy_`, `_academy` | Full-time facility (not garage gym) | Respect scale: 50-200+ students, regular reorders |
| `club`, `team`, `dojo`, `dojang` | Organized group | Mention team/club pricing |
| `kids`, `junior`, `children`, `youth` | Youth programs | Mention kids' gis, junior sizing |
| `bushido`, `budo`, `warrior`, `fight` | Martial philosophy branding | Mirror their language (honor, discipline, respect) |

### Bio/Profile Signals (when visible)
- **Follower count > 1k** → Established, likely has budget
- **Multiple locations mentioned** → Chain expansion opportunity
- **"Head coach", "Professor", "Owner"** → Decision maker in bio
- **Competition posts** → Quality/durability matters
- **Kids' class photos** → Junior gis are a line item

## Personalization Template Structure

### Opening Hook (1 line)
> Saw [Academy/Club Name] — clean [BJJ/Muay Thai/Boxing] program, respect the [bushido mindset/technique focus].

### Value Prop (2-3 lines, sport-specific SKUs)
> We manufacture custom [BJJ gear] in Sialkot for academies like yours:
> • 450g pearl-weave gis — €29.60 landed, your logo/colors
> • Rash guards (SS/LS) — €9.50/€11.50, fully sublimated
> • Belts (all ranks) — €3, woven rank bars
> • Kids' gis from €24

### Terms (1 line)
> **30 pcs MOQ • 4–6 weeks • Door-to-door, zero customs fees**

### CTA (1 question)
> Which items does the academy need most? I'll send mockups + exact quote today.

### Sign-off
> — HSN Warrior Apparels

## Sport-Specific SKU Maps

### BJJ / Jiu-Jitsu
- Gis (pearl weave 450g): €29.60
- Rash guards SS: €9.50 | LS: €11.50
- Belts (all ranks): €3
- Kids' gis: €24
- MMA shorts: €9.90
- MMA tights: €12.50

### Muay Thai / Kickboxing
- Boxing gloves (cowhide): €25.50
- Shin guards (cowhide): €28.50
- Muay Thai shorts: €14.50
- Headgear (cowhide): €24.00

### Boxing
- Boxing gloves (cowhide): €25.50
- Headgear (cowhide): €24.00
- Hand wraps / focus mitts: inquire

### Judo
- Judogi (IJF cut): inquire
- Belts: €3

### Karate / Taekwondo
- Karategi / Dobok: inquire
- Hand/foot gear: inquire

### General / Teamwear
- Hoodies: €14.50
- Training tees: €12.50
- Muay Thai shorts: €14.50

## Anti-Patterns
- ❌ Generic "I hope you're doing well" opening
- ❌ Full 12-SKU dump regardless of sport
- ❌ Sender name ≠ brand name ("My name is X")
- ❌ No hook — why *this* club? Why now?
- ❌ Casual emojis (🙏) in B2B first touch
- ✅ One clear CTA: quantity question
- ✅ Specific value props: MOQ, branding included, tax-free shipping
- ✅ Brand identity: HSN Warrior Apparels, Sialkot, since 2011

## Workflow Integration
1. Hunt/find lead → capture IG handle + profile link
2. Parse handle + bio for sport + facility type
3. Select sport-specific SKU map
4. Generate personalized message using template structure
5. Run through spam_check.py before send
6. Send JPG price list + Vercel PDF link in DM
7. Log handle analysis in leads.csv notes

## Related
- `references/client-reply-templates.md` — base templates
- `references/outreach-channel-mechanics.md` — IG send mechanics
- `references/branded-price-list.md` — JPG/PDF creation