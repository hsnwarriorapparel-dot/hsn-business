#!/usr/bin/env python3
"""Print how many emails went out today (from leads.csv), for shell callers."""
import csv, datetime, sys

DAY = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
rows = list(csv.DictReader(open('/home/ubuntu/leads.csv')))
n = 0
for r in rows:
    st = r.get('Status') or ''
    for part in st.split('|'):
        low = part.lower()
        if ('email sent' in low or 'follow-up sent' in low or 'chain pitch sent' in low) and DAY in part:
            n += 1
            break
print(n)
