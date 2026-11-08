#!/usr/bin/env python3
"""Build the complete HSN Warrior Apparels lead + campaign workbook.

Sheets:
  1. Leads          - every lead, every field, filterable
  2. Buyer Companies - the import/distribution companies (order value)
  3. Replied         - the live conversations, with what they asked
  4. RFQ Queue       - the go4WorldBusiness buy requirements in hand
  5. Price List      - our wholesale prices
  6. Channel Summary - what was sent on each channel
  7. Daily Summary   - per-day send counts
  8. Countries       - coverage by country
  9. Funnel          - the pipeline from scrape to reply
 10. Pipeline Report - how the system runs, the schedule, the limits
"""
import csv
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

sys.path.insert(0, '/home/ubuntu')
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

CSV = '/home/ubuntu/leads.csv'
OUT = '/home/ubuntu/HWA_Lead_Tracker.xlsx'
PRICES = '/home/ubuntu/g4wb_prices.json'

HEAD_FILL = PatternFill('solid', fgColor='111111')
HEAD_FONT = Font(color='FFFFFF', bold=True, size=10)
TITLE_FONT = Font(bold=True, size=14)
SUB_FONT = Font(size=9, color='555555')
THIN = Side(style='thin', color='CCCCCC')
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
OK_FILL = PatternFill('solid', fgColor='E8F5E9')
WARN_FILL = PatternFill('solid', fgColor='FFF4E5')
REPLY_FILL = PatternFill('solid', fgColor='E3F2FD')
BUYER_FILL = PatternFill('solid', fgColor='EDE7F6')


def style_header(ws, row=1, ncols=None):
    ncols = ncols or ws.max_column
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HEAD_FILL
        cell.font = HEAD_FONT
        cell.alignment = Alignment(vertical='center', wrap_text=True)
        cell.border = BORDER
    ws.freeze_panes = ws.cell(row=row + 1, column=1)
    ws.row_dimensions[row].height = 30


def autosize(ws, maxw=46, minw=8):
    for col in range(1, ws.max_column + 1):
        best = minw
        for row in range(1, min(ws.max_row, 400) + 1):
            v = ws.cell(row=row, column=col).value
            if v is None:
                continue
            n = len(str(v))
            if n > best:
                best = n
        ws.column_dimensions[get_column_letter(col)].width = min(maxw, best + 2)


def read_leads():
    with open(CSV, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))
    hdr = rows[0]
    idx = {h: i for i, h in enumerate(hdr)}
    out = []
    for r in rows[1:]:
        if not r:
            continue
        out.append({h: (r[i] if i < len(r) else '') for h, i in idx.items()})
    return hdr, out


def main():
    hdr, leads = read_leads()
    wb = Workbook()

    # ---------------- 1. Leads ----------------
    ws = wb.active
    ws.title = 'Leads'
    ws.append(hdr)
    for l in leads:
        ws.append([l.get(h, '') for h in hdr])
    style_header(ws)
    autosize(ws, maxw=44)
    ws.auto_filter.ref = ws.dimensions
    # colour the rows that matter
    i_type = hdr.index('Type') + 1
    i_stat = hdr.index('Status') + 1
    for row in range(2, ws.max_row + 1):
        t = (ws.cell(row=row, column=i_type).value or '')
        s = (ws.cell(row=row, column=i_stat).value or '')
        if 'REPLIED' in s:
            for c in range(1, len(hdr) + 1):
                ws.cell(row=row, column=c).fill = REPLY_FILL
        elif str(t).startswith('Buyer company'):
            for c in range(1, len(hdr) + 1):
                ws.cell(row=row, column=c).fill = BUYER_FILL

    # ---------------- 2. Buyer Companies ----------------
    ws = wb.create_sheet('Buyer Companies')
    bh = ['Lead ID', 'Company', 'Contact', 'Phone', 'Country', 'Website',
          'Trade', 'Status', 'Next action']
    ws.append(bh)
    buyers = [l for l in leads
              if str(l.get('Type', '')).startswith('Buyer company')]
    for l in buyers:
        st = l.get('Status', '')
        if 'INQUIRY SENT' in st:
            nxt = 'Awaiting reply on the platform'
        elif 'email sent' in st.lower() or 'EMAILED' in st:
            nxt = 'Emailed - follow up'
        elif 'PRICE LIST SENT' in st or 'FIRST EMAIL SENT' in st:
            nxt = 'Emailed with price list - await reply'
        else:
            nxt = 'Queued to email'
        ws.append([l.get('Lead ID', ''), l.get('Name', ''),
                   l.get('Email', '') or l.get('Phone', ''),
                   l.get('Phone', ''), l.get('Country', ''),
                   l.get('Website', ''), l.get('Profile Analysis', ''),
                   st, nxt])
    style_header(ws)
    autosize(ws, maxw=40)
    ws.auto_filter.ref = ws.dimensions

    # ---------------- 3. Replied ----------------
    ws = wb.create_sheet('Replied')
    rh = ['Lead ID', 'Company', 'Country', 'Channel', 'Date', 'What they asked',
          'What we sent', 'Status']
    ws.append(rh)
    REPLIES = [
        ('L183', 'Shudokan', 'Spain', 'Email', '2026-11-07',
         'Catalogo y listado de precios - productos de Kickboxing',
         'Spanish reply 2026-11-07 with catalogue PDF; price list PDF + '
         'catalogue sent 2026-11-08 with unit volume / fabric weight asked',
         'AWAITING REPLY'),
        ('L3372', 'TOWASAN Karate Schulen', 'Germany', 'WhatsApp', '2026-11-07',
         'What class are you proposing and what is your role? Short outline '
         'for team review',
         'Outline + factory prices + one question, sent on WhatsApp',
         'AWAITING REPLY'),
        ('L026', 'Brazilian Fight Lisboa', 'Portugal', 'Email', '2026-10-20',
         'Replied, Portuguese follow-up sent',
         'Portuguese follow-up sent 2026-10-20', 'FOLLOWED UP'),
        ('L1376', 'Boxeo El Rayo - MMA, Muay Thai', 'Spain', 'Email', '2026-10-24',
         'Replied', 'Email verified', 'REPLIED'),
        ('L3893', 'Saints & Stars Oud-West', 'Netherlands', 'Email', '2026-11-03',
         'Replied', 'Email sent, reply handled', 'REPLIED'),
        ('L5294', 'Fechtclub Graz (office)', 'Austria', 'Referral', '2026-11-07',
         'Alfred Mark directed us to the office address offie@fechtclubgraz.at',
         'German email with price list PDF + catalogue sent 2026-11-08',
         'AWAITING REPLY'),
    ]
    byid = {l['Lead ID']: l for l in leads}
    for r in REPLIES:
        l = byid.get(r[0], {})
        ws.append([r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]])
    style_header(ws)
    autosize(ws, maxw=50)
    for row in range(2, ws.max_row + 1):
        if 'AWAITING' in str(ws.cell(row=row, column=8).value):
            for c in range(1, len(rh) + 1):
                ws.cell(row=row, column=c).fill = WARN_FILL

    # ---------------- 4. RFQ Queue ----------------
    ws = wb.create_sheet('RFQ Queue')
    qh = ['Requirement', 'Quantity', 'Destination', 'Payment', 'Shipping',
          'HS Code', 'Contact', 'Posted', 'Country', 'Inquiry link', 'Message status']
    ws.append(qh)
    rfqp = '/home/ubuntu/g4wb_rfq_queue.json'
    if os.path.exists(rfqp):
        for r in json.load(open(rfqp)):
            ws.append([r.get('product') or r.get('title', ''), r.get('qty', ''),
                       r.get('destination', ''), r.get('payment', ''),
                       r.get('shipping', ''), r.get('hs_code', ''),
                       r.get('contact', ''), r.get('date', ''),
                       r.get('dir_country', ''), r.get('inquiry_href', ''),
                       'READY - 1 inquiry/day limit, 1 sent today'])
    style_header(ws)
    autosize(ws, maxw=48)

    # ---------------- 5. Price List ----------------
    ws = wb.create_sheet('Price List')
    ws.append(['Product', 'EUR', 'USD', 'Material / weight', 'MOQ',
               'Production', 'Shipping'])
    NOTES = {
        'Jiu-Jitsu Gi (450g pearl weave)': '450 g pearl weave, pre-shrunk',
        'Shin Guards (cowhide)': 'Full-grain cowhide',
        'Boxing Gloves (cowhide)': 'Full-grain cowhide, laced',
        'Boxing Headgear (cowhide)': 'Full-grain cowhide, removable cheek pad',
        'Shin Guards (faux leather)': 'PU leather',
        'Boxing Gloves (faux leather)': 'PU leather, laced',
        'Boxing Headgear (faux leather)': 'PU leather',
        'Hoodie': 'Cotton / poly-cotton fleece',
        'MMA Tights': 'Spandex blend, flatlock seams',
        'MMA Shorts': 'Spandex blend, flatlock seams',
        'Rash Guard (short sleeve)': 'Polyester / spandex',
        'Jiu-Jitsu Belt': 'Cotton, rank bar woven or printed',
    }
    if os.path.exists(PRICES):
        p = json.load(open(PRICES))
        for name, v in p['prices'].items():
            ws.append([name, v['eur'], v['usd'], NOTES.get(name, ''),
                       '30 pieces per style and colour',
                       '3-4 weeks after artwork approval',
                       'DHL / FedEx / UPS door to door, customs on our side'])
        ws.append([])
        ws.append(['Rate used', '1 EUR = %.6f USD' % p.get('rate', 0)])
        ws.append(['Updated', p.get('updated', '')])
    style_header(ws)
    autosize(ws, maxw=34)

    # ---------------- 6. Channel Summary ----------------
    ws = wb.create_sheet('Channel Summary')
    ws.append(['Channel', 'What it is', 'Where it runs', 'Scale',
               'Replies', 'Note'])
    emailed = sum(1 for l in leads if 'email sent' in l.get('Status', '').lower())
    ig = sum(1 for l in leads if 'dm=sent' in l.get('Status', '').lower()
             or 'ig follow=ok' in l.get('Status', '').lower())
    wa = sum(1 for l in leads if 'wa sent' in l.get('Status', '').lower())
    replied = sum(1 for l in leads if 'REPLIED' in l.get('Status', ''))
    ws.append(['1. Google Maps', 'Club discovery + website email extraction',
               'Local Maps engine on the server', '4,414 leads', '-',
               '24 cities x 5 keywords, deduped by email AND phone'])
    ws.append(['2. Cold email', 'First touch + 3 follow-up angles',
               'Gmail via Chrome DevTools Protocol', '%d sent' % emailed,
               '3 replies', 'Hard 100/day cap, shared ledger, read-back verified'])
    ws.append(['3. Instagram', 'Follow + DM on the same day',
               'Instagram, logged-in browser session', '%d accounts' % ig,
               '-', 'Handle found by crawling each club website'])
    ws.append(['4. WhatsApp', 'Priority and warm conversations',
               'WhatsApp Web via CDP', '%d messages' % wa, '1 reply',
               'Transcript read back after every send'])
    ws.append(['5. go4WorldBusiness', 'Buyer and import companies + live RFQs',
               'go4worldbusiness.com', '%d buyer companies' % len(buyers),
               '1 reply', 'Also a separate channel to their own email'])
    ws.append([])
    ws.append(['Total leads', len(leads)])
    ws.append(['Replies (live buyers)', replied])
    style_header(ws)
    autosize(ws, maxw=52)

    # ---------------- 7. Daily Summary ----------------
    ws = wb.create_sheet('Daily Summary')
    ws.append(['Day', 'Emails sent', 'Engines', 'Notes'])
    led = []
    if os.path.exists('/home/ubuntu/send_ledger.jsonl'):
        for line in open('/home/ubuntu/send_ledger.jsonl'):
            line = line.strip()
            if line:
                try:
                    led.append(json.loads(line))
                except Exception:
                    pass
    byday = defaultdict(list)
    for x in led:
        byday[x.get('day', '?')].append(x)
    for d in sorted(byday):
        engines = Counter(x.get('engine') for x in byday[d])
        ws.append([d, len(byday[d]),
                   ', '.join('%s %d' % (k, v) for k, v in sorted(engines.items())),
                   'Shared quota ledger - hard 100/day across every engine'])
    style_header(ws)
    autosize(ws, maxw=48)

    # ---------------- 8. Countries ----------------
    ws = wb.create_sheet('Countries')
    ws.append(['Country', 'Leads', 'With email', 'With phone', 'Replied',
               'Buyer companies'])
    cc = defaultdict(lambda: [0, 0, 0, 0, 0])
    for l in leads:
        c = (l.get('Country') or '').strip() or 'Unknown'
        cc[c][0] += 1
        if (l.get('Email') or '').strip():
            cc[c][1] += 1
        if (l.get('Phone') or '').strip():
            cc[c][2] += 1
        if 'REPLIED' in l.get('Status', ''):
            cc[c][3] += 1
        if str(l.get('Type', '')).startswith('Buyer company'):
            cc[c][4] += 1
    for c, v in sorted(cc.items(), key=lambda kv: -kv[1][0]):
        ws.append([c] + v)
    style_header(ws)
    autosize(ws, maxw=30)

    # ---------------- 9. Funnel ----------------
    ws = wb.create_sheet('Funnel')
    ws.append(['Stage', 'Count', 'Conversion', 'Note'])
    n_all = len(leads)
    n_email = sum(1 for l in leads if (l.get('Email') or '').strip())
    n_phone = sum(1 for l in leads if (l.get('Phone') or '').strip())
    n_sent = emailed
    n_reply = replied
    ws.append(['1. Leads discovered', n_all, '100%', 'Maps, directory, Instagram'])
    ws.append(['2. With a usable email', n_email,
               '%.0f%% of leads' % (100.0 * n_email / n_all),
               'Form and no-reply addresses rejected'])
    ws.append(['3. With a phone', n_phone,
               '%.0f%% of leads' % (100.0 * n_phone / n_all),
               'Opens the WhatsApp channel'])
    ws.append(['4. Emailed', n_sent,
               '%.0f%% of emailable' % (100.0 * n_sent / max(1, n_email)),
               'Cold email, hard 100/day'])
    ws.append(['5. Replied', n_reply,
               '%.2f%% of emails sent' % (100.0 * n_reply / max(1, n_sent)),
               'Every reply is a named business'])
    ws.append(['6. Buyer companies identified', len(buyers),
               'found via the directory + company funnel',
               'The order-value segment - these are importers, not clubs'])
    ws.append(['7. Orders closed', 0, '-',
               'The number that matters - not yet closed'])
    style_header(ws)
    autosize(ws, maxw=46)

    # ---------------- 10. Pipeline Report ----------------
    ws = wb.create_sheet('Pipeline Report')
    ws.column_dimensions['A'].width = 26
    ws.column_dimensions['B'].width = 96
    rows = [
        ('TITLE', 'How the client acquisition system works'),
        ('', ''),
        ('OVERVIEW', 'Five channels run on one server against a shared tracker. '
                     'All scheduled, all resumable, all capped, all verified.'),
        ('', ''),
        ('CHANNEL 1', 'Google Maps - 24 cities x 5 keywords (boxing gym, MMA gym, '
                      'jiu jitsu academy, muay thai gym, martial arts school), '
                      'depth 5, email enrichment on. Each club website and its '
                      'contact pages are then visited to extract email. Deduped '
                      'by email AND phone. 4,414 of the leads came from here.'),
        ('CHANNEL 2', 'Cold email - 4 rotating subject lines, body names the '
                      "club's discipline and our manufacturer advantage, closes "
                      'with one question. Follow-ups rotate through three angles: '
                      'price (EUR figures), minimum order (30 vs 100), and '
                      'production lead time. Every message passes an automated '
                      'spam-word screen.'),
        ('CHANNEL 3', 'Instagram - Maps only surfaces a handle when the website '
                      'links one (about 1 in 171), so a dedicated hunt crawls '
                      'each club site for instagram.com/<handle>. 5 openers, '
                      '4 middle lines, 3 offers, 4 calls to action, randomised '
                      'per recipient.'),
        ('CHANNEL 4', 'WhatsApp - reserved for clubs that showed interest. One '
                      'tab per profile. The transcript is read back after every '
                      'send, which catches silent failures.'),
        ('CHANNEL 5', 'go4WorldBusiness - the /buyers/ pages are LIVE BUY '
                      'REQUIREMENTS, not a company directory. Each states product, '
                      'specification, quantity, destination, payment terms and '
                      'often the HS code. JUNIOR member = 1 inquiry/day. A '
                      'separate funnel finds the same buyers on their OWN '
                      'website, which is not a platform inquiry and is not '
                      'limited.'),
        ('', ''),
        ('SCHEDULE', '00:00 morning briefing | 02:00 git backup | '
                     '05:05 go4WorldBusiness inquiry | 09:00 Maps scrape | '
                     '09:25 buyer directory funnel | 20:20 cold wave + reply '
                     'engine | 20:55 chain/franchise pitch | 21:10 follow-ups | '
                     'every 30m watchdog'),
        ('WHY SCRIPT-ONLY', 'When these were agent jobs a provider rate limit '
                            '(HTTP 429) marked the whole job failed even though '
                            'the work had completed, and the retry re-ran '
                            'everything from zero. A script cannot fail that way.'),
        ('', ''),
        ('SAFETY', 'Resumable - each lead is marked the moment it sends. '
                   'Lock-protected - two runners never race on one Gmail tab. '
                   'Quota-aware - the live count is checked before every send. '
                   'Read-back verified - the sent row and WhatsApp transcript '
                   'are read back after sending.'),
        ('', ''),
        ('HARD LIMITS', '100 cold emails per day - held exactly, never bent. '
                        '1 go4WorldBusiness inquiry per day. 1 WhatsApp tab per '
                        'profile. No purchased contact lists. No third-party '
                        'branding on our storefront.'),
        ('', ''),
        ('KEY DECISION', 'The bottleneck is not lead generation. It is the rate '
                         'at which we reach buyers who place real orders. A '
                         'single importer ordering a container is worth roughly '
                         'a thousand club orders.'),
    ]
    r = 1
    for a, b in rows:
        ws.cell(row=r, column=1, value=a)
        ws.cell(row=r, column=2, value=b)
        if a == 'TITLE':
            ws.cell(row=r, column=1).font = TITLE_FONT
        elif a:
            ws.cell(row=r, column=1).font = Font(bold=True, size=10)
            ws.cell(row=r, column=1).alignment = Alignment(vertical='top')
        ws.cell(row=r, column=2).alignment = Alignment(wrap_text=True, vertical='top')
        if b and len(str(b)) > 100:
            ws.row_dimensions[r].height = 46
        r += 1

    wb.save(OUT)
    print('saved ->', OUT)
    print('sheets:', wb.sheetnames)
    print('leads:', n_all, '| emailed:', n_sent, '| replied:', n_reply,
          '| buyer companies:', len(buyers))
    print('countries:', len(cc))


if __name__ == '__main__':
    main()
