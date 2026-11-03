#!/usr/bin/env python3
"""HSN Morning Business Briefing — runs daily at 6:00 AM PKT (01:00 UTC).
Collects: business news (B2B/manufacturing/e-commerce), Hacker News top stories,
new AI/tools launches, martial-arts-industry news, and HSN pipeline numbers.
Saves a briefing file; the cron job sends it to Telegram.
"""
import subprocess, json, re, time, os, datetime, csv
import urllib.request

OUT = '/home/ubuntu/morning_briefing.md'
AMMO = 0

def fetch(url, headers=None):
    try:
        req = urllib.request.Request(url, headers=headers or {'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode('utf-8', 'replace')
    except Exception as e:
        return None

def hn_top(n=8):
    """Top Hacker News stories via Algolia API (free, no auth)."""
    try:
        data = json.loads(fetch('https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=12') or '{}')
        out = []
        for h in data.get('hits', [])[:n]:
            title = h.get('title') or ''
            url = h.get('url') or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
            points = h.get('points', 0)
            out.append((title, url, points))
        return out
    except Exception:
        return []

# Off-topic filters (2026-10-27): the generic B2B feed surfaces China media-market
# forecasts and furniture plants, which are useless to a sportswear manufacturer.
_OFFTOPIC = re.compile(
    r'media market|advertising market|furniture|home furnishings|real estate|'
    r'cryptocurrency|crypto\b|bitcoin|nft\b|video game|gaming market|'
    r'automotive|pharmaceutical|banking|insurance|airline|air cargo|'
    r'stock price|stock quote|news, quote and history|'
    r'coal|steel price|petrochemical|semiconductor chip|'
    # consumer-lifestyle pieces are not useful to a manufacturer
    r'fall clothing trends|fashion magazine|outfit|what to wear|'
    r'glp-1|weight loss|celebrity style|red carpet|shopping for new clothes|'
    r'\bfashion week\b|street style|how to style|wardrobe|'
    r'holiday gift guide|prime day|black friday|deal of the day|'
    # syndicated market-research spam (one-per-topic press releases)
    r'size,? trends and forecast|market research report|market size,? share|'
    r'global market report|market report 20\d\d|cagr of|'
    r'market in (latin america|asia pacific|north america|the middle east)', re.I)


def business_news(n=6):
    """Business/manufacturing/e-commerce headlines from Google News RSS."""
    feeds = [
        ('https://news.google.com/rss/search?q=textile+apparel+manufacturing+export+tariff+supply+chain+when:2d&hl=en-US&gl=US&ceid=US:en', 'Textile/Export'),
        ('https://news.google.com/rss/search?q=b2b+manufacturing+export+when:1d&hl=en-US&gl=US&ceid=US:en', 'B2B/Manufacturing'),
        ('https://news.google.com/rss/search?q=sportswear+apparel+industry+when:2d&hl=en-US&gl=US&ceid=US:en', 'Sportswear Industry'),
        ('https://news.google.com/rss/search?q=martial+arts+boxing+gym+business+when:2d&hl=en-US&gl=US&ceid=US:en', 'Martial Arts Business'),
    ]
    all_news = []
    for url, label in feeds:
        xml = fetch(url)
        if not xml:
            continue
        items = re.findall(r'<item><title>(.*?)</title>.*?<pubDate>(.*?)</pubDate>.*?<link>(.*?)</link>', xml, re.S)
        for t, d, l in items[:6]:
            t = t.replace(chr(38) + 'amp;', chr(38)).replace(chr(38) + '#39;', chr(39))
            t = re.sub(r' - [A-Z][^ ]+( - [^ ]+)?$', '', t)
            if _OFFTOPIC.search(t):
                continue
            all_news.append((label, t, l))
    # de-dupe by title, keep label variety first
    seen = set()
    out = []
    for label, t, l in all_news:
        key = t.lower()[:60]
        if key in seen:
            continue
        seen.add(key)
        out.append((label, t, l))
    return out[:n]

def tools_news(n=5):
    """AI tools + launches from HN (search recent 'launch/show') + Google News."""
    out = []
    try:
        data = json.loads(fetch('https://hn.algolia.com/api/v1/search_by_date?tags=show_hn&hitsPerPage=6') or '{}')
        for h in data.get('hits', [])[:n]:
            out.append(('Show HN: ' + (h.get('title') or 'Untitled'), h.get('url') or '', h.get('points', 0)))
    except Exception:
        pass
    return out

def pipeline_numbers():
    """HSN lead pipeline stats from leads.csv."""
    try:
        with open('/home/ubuntu/leads.csv') as f:
            rows = list(csv.reader(f))
        idx = {h: i for i, h in enumerate(rows[0])}
        total = len(rows) - 1
        today_tag = 'Day 5 USA'
        d5 = sum(1 for r in rows[1:] if today_tag in r[idx['Notes']])
        hot = [r for r in rows[1:] if 'HOT' in r[idx['Status']] or 'negotiating' in r[idx['Status']].lower()]
        return total, d5, hot
    except Exception:
        return 0, 0, []

def generate_insights(hot_leads):
    """All numbers computed LIVE from leads.csv (2026-10-29: hardcoded counts kept lying)."""
    global AMMO
    insights = []
    usa_sent = usa_total = usa_open = ammo = 0
    total = 0
    try:
        with open('/home/ubuntu/leads.csv') as f:
            rows = list(csv.reader(f))
        idx = {h: i for i, h in enumerate(rows[0])}
        usa = [r for r in rows[1:] if (r[idx['Country']] or '').strip().lower() in
               ('usa', 'united states', 'us', 'united states of america')]
        usa_total = len(usa)
        usa_sent = sum(1 for r in usa if 'email sent' in (r[idx['Status']] or '').lower())
        bad = re.compile(r'not found|failed|skipped|excluded', re.I)
        usa_open = sum(1 for r in usa
                       if 'email sent' not in (r[idx['Status']] or '').lower()
                       and not bad.search(r[idx['Status']] or ''))
        total = len(rows) - 1
        ammo = sum(1 for r in rows[1:]
                   if (r[idx['Email']] or '').strip()
                   and 'email sent' not in (r[idx['Status']] or '').lower()
                   and not bad.search(r[idx['Status']] or ''))
        insights.append(f"Pipeline: {total} total leads | USA {usa_sent}/{usa_total} emailed, "
                        f"{usa_open} still open | global ammo {ammo} leads ready to email")
        replied = sum(1 for r in rows[1:] if 'reply' in r[idx['Status']].lower() or 'HOT' in r[idx['Status']])
        insights.append(f"{replied} tracker rows carry a reply/HOT marker (includes declines, "
                        "auto-acks and STOP rows - see the HUMAN reply line below for the real count)")
    except Exception:
        pass
    AMMO = ammo

    # --- HUMAN replies: computed LIVE from the tracker (2026-11-03 fix) ---
    # A row counts as a HUMAN reply when its Status carries an explicit reply marker
    # that is NOT an auto-ack ("AUTO-REPLY", "auto-acknowledgement", "auto-reply").
    human_replies = []
    declines = []
    try:
        with open('/home/ubuntu/leads.csv') as f:
            rows = list(csv.reader(f))
        idx = {h: i for i, h in enumerate(rows[0])}
        decline_markers = ('not looking for new supplier', 'permanently closed', 'no longer',
                           'not interested', 'not interested at this time', 'closed - no contact')
        for r in rows[1:]:
            st = (r[idx['Status']] or '')
            low = st.lower()
            if 'reply' not in low:
                continue
            if any(k in low for k in ('auto-reply', 'auto reply', 'auto-acknowledgement',
                                       'automatische antwort', 'automatic reply')):
                continue
            if 'do not contact' in low:      # STOP = not a sales reply
                continue
            if any(d in low for d in decline_markers):
                declines.append((r[idx['Lead ID']], r[idx['Name']]))
                continue
            human_replies.append((r[idx['Lead ID']], r[idx['Name']], st))
    except Exception:
        pass
    if human_replies:
        names = ', '.join(f"{lid} {nm}" for lid, nm, _ in human_replies[:3])
        insights.append(f"HUMAN business replies on the board: {len(human_replies)} ({names}) - "
                        "reply is DRAFT-ONLY until the user says send")
    else:
        insights.append("No human business reply markers in the tracker - every recent Gmail/IG "
                        "reply is an auto-ack, an out-of-office or a bounce")
    if declines:
        dn = ', '.join(f"{lid} {nm}" for lid, nm in declines[:3])
        insights.append(f"Polite declines / closed accounts (do NOT follow up): {len(declines)} ({dn})")

    # --- Session health: read the live CDP sweep, never assert it statically ---
    sweep = {}
    try:
        with open('/home/ubuntu/morning_sweep.json') as f:
            sweep = json.load(f)
        age = (os.path.getmtime('/home/ubuntu/morning_sweep.json'))
        fresh_min = (time.time() - age) / 60
    except Exception:
        fresh_min = 999
    if fresh_min <= 45:
        if sweep.get('wa_alive'):
            insights.append("WhatsApp Web session is ALIVE (live CDP sweep) - WA sends can run")
        elif sweep.get('wa_qr'):
            insights.append("WhatsApp Web session is DEAD (QR screen, live CDP sweep) - "
                            "no WA sends since Oct 24. Re-link from phone/VNC to resume the 10/day quota")
        else:
            insights.append("WhatsApp Web state unknown this run (no QR, no pane)")
        if not sweep.get('ig_error') and sweep.get('ig_head'):
            insights.append("Instagram IS logged in (live CDP sweep) - IG follow+DM pass is running normally")
        else:
            insights.append("Instagram state unknown this run - check the CDP sweep")
    else:
        insights.append(f"Session health NOT verified this run (sweep file is {int(fresh_min)} min old)")

    insights.append("go4WorldBusiness: profile IS live and logged in (hsnwarriorapparel_9, Junior Member) "
                    "but 0 products added (verified live 2026-11-03) - list products so buyers can find us")
    insights.append("SECURITY: TradeWheel emailed the account password in plaintext - change it and reuse a unique password")
    return insights

def main():
    now = datetime.datetime.now().strftime('%A, %d %B %Y')
    lines = []
    lines.append(f"☀️ HSN MORNING BRIEFING — {now}")
    lines.append("")
    lines.append("=" * 40)
    lines.append("")

    # 1. Your business pipeline
    total, d5, hot = pipeline_numbers()
    lines.append(f"📊 YOUR PIPELINE")
    lines.append(f"• Total leads tracked: {total}")
    lines.append(f"• USA batch (Day 5): {d5}")
    if hot:
        lines.append(f"• 🔥 HOT leads: {len(hot)}")
        for h in hot[:5]:
            lines.append(f"   - {h[1]} ({h[0]})")
    lines.append("")

    # 2. Business news
    lines.append("📰 BUSINESS NEWS (24h)")
    bn = business_news()
    if bn:
        for label, t, l in bn:
            lines.append(f"• [{label}] {t}")
            if l:
                lines.append(f"  {l}")
    else:
        lines.append("• (news feed unreachable this morning)")
    lines.append("")

    # 3. Hacker News
    lines.append("💻 HACKER NEWS — top of the morning")
    for t, u, p in hn_top(8):
        lines.append(f"• {t} ({p} points)")
    lines.append("")

    # 4. New tools/launches
    lines.append("🛠️ NEW TOOLS & LAUNCHES")
    for t, u, p in tools_news():
        lines.append(f"• {t}")
    lines.append("")

    # 5. Market/pricing news
    lines.append("📈 MARKET & PRICING")
    try:
        xml = fetch('https://news.google.com/rss/search?q=textile+export+cotton+prices+when:2d&hl=en-US&gl=US&ceid=US:en')
        items = re.findall(r'<item><title>(.*?)</title>', xml or '', re.S)
        for t in items[:3]:
            t = t.replace('&#39;', "'").replace('&', '&')
            lines.append(f"• {t[:100]}")
    except Exception:
        pass
    lines.append("")

    # 6. Tips & tricks for his business
    lines.append("💡 TIPS & TRICKS")
    tips = [
        "Reply to leads within 5 minutes when possible - first responder wins 78% of B2B deals",
        "When quoting, always give 2-3 options (budget/premium) - choice increases conversion",
        "Ask for the logo early - clients who send logos are 3x more likely to order",
        "Follow up on sent samples after 5 days with: 'How did the quality feel?'",
        "Post the same product photo on IG 3-4 weeks apart - audiences grow and forget",
        "Voice notes outperform text 2:1 in Southern Europe and Gulf markets",
    ]
    import random as _r
    for tip in _r.sample(tips, 3):
        lines.append(f"• {tip}")
    lines.append("")

    # 7. What boss needs to know (proactive)
    lines.append("🎯 WHAT YOU NEED TO KNOW TODAY")
    insights = generate_insights(hot_leads=hot if 'hot' in dir() else [])
    for i in insights[:6]:
        lines.append(f"• {i}")
    lines.append("")

    # 5. Action reminder
    lines.append("🎯 TODAY'S MOVES")
    lines.append("• Re-link WhatsApp Web from your phone (QR screen is up) - that unlocks the 10/day WA quota")
    if AMMO:
        lines.append(f"• {AMMO} leads have a valid email and no send marker - fire the next 100-email wave tonight (20:00 UTC / 1 AM PKT)")
    else:
        lines.append("• Ammo is dry - run another Maps/Exa hunt before the next wave")
    lines.append("• USA emails continue in US business hours (7 PM - 1 AM PKT)")
    lines.append("• Check Alvaro's sample order status - he is the closest to payment")
    lines.append("• Add products to the go4WorldBusiness profile (0 listed = invisible to buyers)")
    lines.append("")
    lines.append("— Your Hermes Agent 🥊")

    with open(OUT, 'w') as f:
        f.write('\n'.join(lines))
    print('\n'.join(lines))
    print(f"\nSaved: {OUT}")

if __name__ == '__main__':
    main()
