#!/usr/bin/env python3
"""Rebuild HWA_Lead_Tracker.xlsx from leads.csv (15-col schema) + refresh WA_Pending_List via make_wa_excel."""
import csv
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

CSV = '/home/ubuntu/leads.csv'
OUT = '/home/ubuntu/HWA_Lead_Tracker.xlsx'

with open(CSV) as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = [r for r in reader]

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Leads"

# header
hdr_fill = PatternFill(start_color="1F4E4F", end_color="1F4E4F", fill_type="solid")
hdr_font = Font(color="FFFFFF", bold=True, size=11)
for ci, h in enumerate(header, 1):
    c = ws.cell(row=1, column=ci, value=h)
    c.fill = hdr_fill
    c.font = hdr_font
    c.alignment = Alignment(horizontal="center")

# data
hot_fill = PatternFill(start_color="FFE8A3", end_color="FFE8A3", fill_type="solid")
for ri, r in enumerate(rows, 2):
    for ci, v in enumerate(r, 1):
        ws.cell(row=ri, column=ci, value=v)
    # highlight HOT leads
    status = r[header.index('Status')] if len(r) > header.index('Status') else ''
    if 'HOT' in status.upper():
        for ci in range(1, len(header)+1):
            ws.cell(row=ri, column=ci).fill = hot_fill

# widths
widths = {'Lead ID': 8, 'Name': 26, 'Type': 12, 'IG Username': 22, 'IG Profile Link': 30,
          'City': 14, 'Country': 12, 'Phone': 16, 'Phone Type': 10, 'Email': 34,
          'Website': 28, 'Status': 46, 'Profile Analysis': 40, 'Products Needed': 20, 'Notes': 36}
for ci, h in enumerate(header, 1):
    ws.column_dimensions[get_column_letter(ci)].width = widths.get(h, 18)
ws.freeze_panes = "A2"
ws.auto_filter.ref = f"A1:{get_column_letter(len(header))}{len(rows)+1}"

# summary sheet
s = wb.create_sheet("Summary")
usa = [r for r in rows if 'USA' in (r[header.index('Country')] if len(r) > header.index('Country') else '')]
s['A1'] = "HSN Warrior Apparels — Lead Tracker Summary"
s['A1'].font = Font(bold=True, size=13)
s['A3'] = "Generated (UTC):"; s['B3'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
s['A4'] = "Total leads:"; s['B4'] = len(rows)
s['A5'] = "USA batch:"; s['B5'] = len(usa)
s['A6'] = "USA emails sent:"; s['B6'] = sum(1 for r in usa if 'email sent' in (r[header.index('Status')] if len(r) > header.index('Status') else ''))
s['A7'] = "USA IG follow/DM done:"; s['B7'] = sum(1 for r in usa if ('follow' in (r[header.index('Status')] if len(r) > header.index('Status') else '').lower() or 'dm=sent' in (r[header.index('Status')] if len(r) > header.index('Status') else '')))
s['A8'] = "HOT leads:"; s['B8'] = sum(1 for r in rows if 'HOT' in (r[header.index('Status')] if len(r) > header.index('Status') else '').upper())

wb.save(OUT)
print(f"Tracker rebuilt: {OUT}")
print(f"  {len(rows)} leads, {len(usa)} USA")
print(f"  USA emails sent: {s['B6'].value} | USA IG done: {s['B7'].value} | HOT: {s['B8'].value}")
