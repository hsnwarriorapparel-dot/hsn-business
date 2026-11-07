# Daily Runbook - HSN Warrior Apparels

Complete daily procedure for the autonomous growth system.

## Morning (5:00 AM PKT - Cron)
1. **Morning Briefing** (`/home/ubuntu/morning_briefing.py`)
   - Pipeline numbers from leads.csv
   - Business news + Hacker News + market prices
   - Client reply sweep (WA/Gmail/IG) → draft replies
   - Deliver to Telegram (deliver=origin)

2. **Infrastructure Check**
   - Browser stack: `ps aux | grep -E "Xvnc|chromium"`
   - CDP port 9222: `curl http://localhost:9222/json/list`
   - Google Maps Scraper API: `curl localhost:8080/api/v1/jobs`
   - Listmonk: `curl localhost:9000`
   - Firecrawl: `docker ps | grep firecrawl`

## Mid-Morning (Manual)
1. **Check overnight cron log**: `tail /home/ubuntu/daily_automation_cron.log`
2. **Verify tracker**: `python3 -c "import csv; ..."` (count SENT emails/IG/WA)
3. **Review replies**: Check Gmail/Instagram/WhatsApp for client replies
4. **Forward replies to agent** for response drafting

## Daily Automation (9:00 AM - Cron)
Runs `/home/ubuntu/daily_automation_cron.sh`:
1. **Scrape** → Google Maps (2 cities × 5 sports)
2. **Clean** → `process_leads.py` (dedupe, enrich, sport detection)
3. **Generate** → 137 `.eml` + IG DM scripts + tracker CSV
4. **Send Email** → 50 emails via Gmail CDP
5. **Send IG DM** → 20 DMs via Instagram CDP
6. **Send WhatsApp** → 10 messages via CDP
7. **Track** → Update outreach_tracker.csv
8. **Backup** → Git commit + push

## Evening (Manual)
1. **Check day's results**: Review cron log + tracker
2. **Reply to clients**: Send drafted responses from Gmail/phone
3. **Approve mockups/quotes** for hot leads
4. **Scan WhatsApp QR** if session expired (monthly)

## Key Files
| File | Purpose |
|------|---------|
| `/home/ubuntu/gmaps-output/outreach_tracker.csv` | Master tracker (273 rows) |
| `/home/ubuntu/gmaps-output/drafts/*.eml` | Email drafts (137) |
| `/home/ubuntu/gmaps-output/ig_dm_drafts.txt` | IG DM scripts (137) |
| `/home/ubuntu/daily_automation_cron.log` | Cron execution log |
| `/home/ubuntu/daily_automation_full.py` | Master orchestrator |
| `/home/ubuntu/daily_automation_cron.sh` | Cron wrapper |

## Verification Commands
```bash
# Count emails sent today
grep -c "email sent.*$(date +%Y-%m-%d)" /home/ubuntu/gmaps-output/outreach_tracker.csv

# Count total SENT emails
python3 -c "import csv; f=open('/home/ubuntu/gmaps-output/outreach_tracker.csv'); r=csv.DictReader(f); print(sum(1 for row in r if row['Email Sent']=='SENT'))"

# Check cron status
tail -20 /home/ubuntu/daily_automation_cron.log

# Verify browser stack
ps aux | grep -E 'Xvnc|chromium'
curl -s http://localhost:9222/json/list | python3 -c "import json,sys; print(len(json.load(sys.stdin)), 'tabs')"
```

## Troubleshooting
| Issue | Fix |
|-------|-----|
| Cron log shows ModuleNotFoundError | Use Hermes Python in cron wrapper |
| CDP connection refused | Restart browser stack: `/home/ubuntu/vps_boot.sh` |
| Gmail CDP fails | Check Gmail tab exists in CDP list |
| IG DM not sending | Profile URL mapping needs refinement |
| WA not sending | Phone format normalization needed |
| Tracker not updating | Check CSV write permissions |
| Git backup fails | No git repo in /home/ubuntu (expected) |

## Weekly
- Monday: Review pipeline metrics, adjust city rotation
- Wednesday: Check WA session health (QR scan if needed)
- Friday: Review hot leads, approve mockups/quotes
- Monthly: Rotate WA number if banned, update product photos