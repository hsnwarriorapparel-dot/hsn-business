#!/usr/bin/env python3
"""HSN Morning Business Briefing — runs daily at 6:00 AM PKT (01:00 UTC).
Collects: business news (B2B/manufacturing/e-commerce), Hacker News top stories,
new AI/tools launches, martial-arts-industry news, and HSN pipeline numbers.
Saves a briefing file; the cron job sends it to Telegram.
"""
import subprocess, json, re, time, os, datetime, csv
import urllib.request

OUT = '/home/ubuntu/morning_briefing.md'

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

def business_news(n=6):
    """Business/manufacturing/e-commerce headlines from Google News RSS."""
    feeds = [
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
        for t, d, l in items[:3]:
            t = t.replace('&', '&').replace('&#39;', "'").replace('"', '"')
            t = re.sub(r' - [A-Z][^ ]+( - [^ ]+)?$', '', t)
            all_news.append((label, t, l))
        if len(all_news) >= n:
            break
    return all_news[:n]

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
    insights = []
    try:
        with open('/home/ubuntu/leads.csv') as f:
            rows = list(csv.reader(f))
        idx = {h: i for i, h in enumerate(rows[0])}
        d5 = sum(1 for r in rows[1:] if 'Day 5 USA' in r[14])
        total = len(rows) - 1
        insights.append(f"Pipeline: {total} total leads, {d5} USA leads waiting for email wave results")
        # count replied
        replied = sum(1 for r in rows[1:] if 'reply' in r[idx['Status']].lower() or 'HOT' in r[idx['Status']])
        insights.append(f"{replied} leads have engaged so far - these are your warmest targets today")
    except Exception:
        pass
    insights.append("Check the 79 unread Gmail emails - the USA wave sent 200 emails, replies may already be coming")
    insights.append("Instagram login still needed for the IG follow-up phase of the USA campaign")
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
    for i in insights[:4]:
        lines.append(f"• {i}")
    lines.append("")

    # 5. Action reminder
    lines.append("🎯 TODAY'S MOVES")
    lines.append("• Check client replies (Alvaro quantities?)")
    lines.append("• USA emails continue in US business hours (7 PM - 1 AM PKT)")
    lines.append("• 10 WA max, warm-up protocol")
    lines.append("")
    lines.append("— Your Hermes Agent 🥊")

    with open(OUT, 'w') as f:
        f.write('\n'.join(lines))
    print('\n'.join(lines))
    print(f"\nSaved: {OUT}")

if __name__ == '__main__':
    main()
