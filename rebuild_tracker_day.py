#!/usr/bin/env python3
"""Rebuild HWA_Lead_Tracker.xlsx from leads.csv with a per-day summary sheet.
Read-only on the CSV. Prints a read-back verification of the saved workbook."""
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
import sys
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

sys.path.insert(0, '/home/ubuntu')
import hsn_counters as counters

CSV = '/home/ubuntu/leads.csv'
OUT = '/home/ubuntu/HWA_Lead_Tracker.xlsx'

with open(CSV, encoding='utf-8', errors='replace') as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = [r for r in reader]
H = {h: i for i, h in enumerate(header)}


def g(r, key):
    i = H.get(key)
    return r[i] if i is not None and i < len(r) else ''


wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Leads"

hdr_fill = PatternFill(start_color="1F4E4F", end_color="1F4E4F", fill_type="solid")
hdr_font = Font(color="FFFFFF", bold=True, size=11)
for ci, h in enumerate(header, 1):
    c = ws.cell(row=1, column=ci, value=h)
    c.fill = hdr_fill
    c.font = hdr_font
    c.alignment = Alignment(horizontal="center")

hot_fill = PatternFill(start_color="FFE8A3", end_color="FFE8A3", fill_type="solid")
s_index = H.get('Status', 11)
for ri, r in enumerate(rows, 2):
    for ci, v in enumerate(r, 1):
        ws.cell(row=ri, column=ci, value=v)
    st = r[s_index] if s_index < len(r) else ''
    if 'HOT' in st.upper():
        for ci in range(1, len(header) + 1):
            ws.cell(row=ri, column=ci).fill = hot_fill

widths = {'Lead ID': 8, 'Name': 26, 'Type': 12, 'IG Username': 22, 'IG Profile Link': 30,
          'City': 14, 'Country': 12, 'Phone': 16, 'Phone Type': 10, 'Email': 34,
          'Website': 28, 'Status': 46, 'Profile Analysis': 40, 'Products Needed': 20,
          'Notes': 36}
for ci, h in enumerate(header, 1):
    ws.column_dimensions[get_column_letter(ci)].width = widths.get(h, 18)
ws.freeze_panes = "A2"
ws.auto_filter.ref = f"A1:{get_column_letter(len(header))}{len(rows)+1}"

# ---------------- Summary sheet ----------------
s = wb.create_sheet("Summary")
s['A1'] = "HSN Warrior Apparels — Lead Tracker Summary"
s['A1'].font = Font(bold=True, size=13)
s['A3'] = "Generated (UTC):"
s['B3'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')

def ig_done(r):
    return counters.ig_ok(r)


def wa_sent(r):
    return counters.wa_ok(r)


def email_sent(r):
    return counters.email_ok(r)


stats = [
    ("Total leads:", len(rows)),
    ("With email:", sum(1 for r in rows if g(r, 'Email').strip())),
    ("Emails sent (total):", sum(1 for r in rows if email_sent(r))),
    ("Emails failed:", sum(1 for r in rows if 'failed' in g(r, 'Status').lower())),
    ("IG follow+DM done:", sum(1 for r in rows if ig_done(r))),
    ("WhatsApp sent:", sum(1 for r in rows if wa_sent(r))),
    ("HOT leads:", sum(1 for r in rows if 'HOT' in g(r, 'Status').upper())),
    ("Leads with phone:", sum(1 for r in rows if g(r, 'Phone').strip())),
    ("USA leads:", sum(1 for r in rows if 'USA' in g(r, 'Country'))),
]
r0 = 4
summary_cells = {}
for i, (k, v) in enumerate(stats):
    s.cell(row=r0 + i, column=1, value=k).font = Font(bold=True)
    s.cell(row=r0 + i, column=2, value=v)
    summary_cells[k] = f"B{r0 + i}"

# ---------------- Day summary sheet ----------------
d = wb.create_sheet("Day Summary")
d['A1'] = "Daily outreach summary by day tag"
d['A1'].font = Font(bold=True, size=13)
d['A3'] = "Day tag"
d['C3'] = "Leads"
d['D3'] = "Emails sent"
d['E3'] = "IG follow+DM"
d['F3'] = "WhatsApp sent"
for c in range(1, 7):
    d.cell(row=3, column=c).font = Font(bold=True, color="FFFFFF")
    d.cell(row=3, column=c).fill = PatternFill("solid", fgColor="1F4E4F")

day_re = __import__('re').compile(r'(Day[- ]?\d+[^|;,)]*|Daily \d{4}-\d{2}-\d{2}|'
                                   r'HUNTED \(gmaps 2PM [\d-]+\))', __import__('re').I)
buckets = defaultdict(lambda: {"leads": 0, "email": 0, "ig": 0, "wa": 0})
for r in rows:
    st = g(r, 'Status')
    tags = set()
    for m in day_re.finditer(st):
        t = m.group(1).strip()
        t = ' '.join(t.split())
        if t:
            tags.add(t)
    for t in tags:
        b = buckets[t]
        b["leads"] += 1
        sl = st.lower()
        if email_sent(r):
            b["email"] += 1
        if ig_done(r):
            b["ig"] += 1
        if wa_sent(r):
            b["wa"] += 1

rr = 4
for t in sorted(buckets, key=lambda x: (-buckets[x]["leads"], x)):
    b = buckets[t]
    d.cell(row=rr, column=1, value=t)
    d.cell(row=rr, column=3, value=b["leads"])
    d.cell(row=rr, column=4, value=b["email"])
    d.cell(row=rr, column=5, value=b["ig"])
    d.cell(row=rr, column=6, value=b["wa"])
    rr += 1
for col, w in {'A': 34, 'B': 3, 'C': 10, 'D': 14, 'E': 15, 'F': 16}.items():
    d.column_dimensions[col].width = w
d.freeze_panes = "A4"

# ---------------- Country breakdown ----------------
c = wb.create_sheet("Countries")
c['A1'] = "Leads by country"
c['A1'].font = Font(bold=True, size=13)
cc = Counter((g(r, 'Country') or '?').strip() for r in rows)
c['A3'] = "Country"
c['B3'] = "Leads"
c['C3'] = "Emails sent"
for col in range(1, 4):
    c.cell(row=3, column=col).font = Font(bold=True, color="FFFFFF")
    c.cell(row=3, column=col).fill = PatternFill("solid", fgColor="1F4E4F")
rr = 4
for k, v in cc.most_common():
    c.cell(row=rr, column=1, value=k)
    c.cell(row=rr, column=2, value=v)
    c.cell(row=rr, column=3, value=sum(1 for r in rows
                                        if (g(r, 'Country') or '?').strip() == k
                                        and email_sent(r)))
    rr += 1
for col, w in {'A': 20, 'B': 10, 'C': 14}.items():
    c.column_dimensions[col].width = w

wb.save(OUT)

# ---------------- read-back verification ----------------
wb2 = openpyxl.load_workbook(OUT, read_only=True)
wsl = wb2["Leads"]
n_rows = wsl.max_row - 1
days = wb2["Day Summary"]
print(f"Tracker rebuilt: {OUT}")
print(f"  Leads sheet rows (read-back): {n_rows} (csv rows {len(rows)})")
print(f"  Sheets: {wb2.sheetnames}")
print(f"  Summary: total={s[summary_cells['Total leads:']].value}, "
      f"emails sent={s[summary_cells['Emails sent (total):']].value}, "
      f"IG={s[summary_cells['IG follow+DM done:']].value}, "
      f"WA={s[summary_cells['WhatsApp sent:']].value}")
print(f"  Day Summary rows: {days.max_row - 3}")
wb2.close()
