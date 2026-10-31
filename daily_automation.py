#!/usr/bin/env python3
"""
Master Daily Automation Orchestrator
Runs the complete pipeline: scrape -> clean -> generate -> send -> track
"""

import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

def run_cmd(cmd, cwd=None, timeout=600):
    """Run command and return result"""
    print(f"🔧 Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        if result.stdout:
            print(result.stdout[-2000:])  # Last 2000 chars
        if result.stderr:
            print(f"STDERR: {result.stderr[-1000:]}")
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout: {cmd}")
        return False, "", "Timeout"
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, "", str(e)

def main():
    print("=" * 60)
    print(f"🤖 DAILY AUTOMATION STARTED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    BASE = "/home/ubuntu"
    
    # Step 1: Scrape new leads (rotate cities)
    print("\n📍 STEP 1: Google Maps Scraping")
    success, _, _ = run_cmd(f"cd {BASE} && python3 gmaps_daily_scrape.py", timeout=1800)
    if not success:
        print("⚠️ Scraping had issues, continuing...")
    
    # Step 2: Clean and enrich leads
    print("\n🧹 STEP 2: Clean & Enrich Leads")
    success, _, _ = run_cmd(f"cd {BASE} && python3 process_leads.py", timeout=300)
    if not success:
        print("⚠️ Cleaning had issues, continuing...")
    
    # Step 3: Send Emails (CDP)
    print("\n📧 STEP 3: Send Emails via Gmail CDP")
    success, _, _ = run_cmd(f"cd {BASE} && python3 email_sender_cdp.py", timeout=1800)
    if not success:
        print("⚠️ Email sending had issues, continuing...")
    
    # Step 4: Send IG DMs (CDP)
    print("\n📱 STEP 4: Send IG DMs via Instagram CDP")
    success, _, _ = run_cmd(f"cd {BASE} && python3 ig_dm_sender_cdp.py", timeout=1800)
    if not success:
        print("⚠️ IG DM sending had issues, continuing...")
    
    # Step 5: Send WhatsApp (CDP)
    print("\n💬 STEP 5: Send WhatsApp via CDP")
    success, _, _ = run_cmd(f"cd {BASE} && python3 wa_sender_cdp.py", timeout=1800)
    if not success:
        print("⚠️ WhatsApp sending had issues, continuing...")
    
    # Step 6: Git backup
    print("\n💾 STEP 6: Git Backup")
    run_cmd(f"cd {BASE} && git add -A && git commit -m 'Daily automation {datetime.now().strftime('%Y-%m-%d')}' && git push", timeout=120)
    
    # Step 7: Report summary
    print("\n📊 STEP 7: Generate Report")
    # Count results
    drafts = len(list(Path(f"{BASE}/gmaps-output/drafts").glob("*.eml"))) if Path(f"{BASE}/gmaps-output/drafts").exists() else 0
    
    import csv
    tracker_rows = 0
    sent_emails = 0
    sent_ig = 0
    sent_wa = 0
    if Path(f"{BASE}/gmaps-output/outreach_tracker.csv").exists():
        with open(f"{BASE}/gmaps-output/outreach_tracker.csv", 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tracker_rows += 1
                if row.get('Email Sent') == 'SENT':
                    sent_emails += 1
                if row.get('IG DM Sent') == 'SENT':
                    sent_ig += 1
                if row.get('WA Sent') == 'SENT':
                    sent_wa += 1
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    DAILY AUTOMATION REPORT                     ║
╠══════════════════════════════════════════════════════════════╣
║ Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                                    ║
║                                                                ║
║ 📧 Emails Sent: {sent_emails}                                               ║
║ 📱 IG DMs Sent: {sent_ig}                                                ║
║ 💬 WhatsApp Sent: {sent_wa}                                             ║
║ 📊 Tracker Rows: {tracker_rows}                                           ║
║ 📝 Drafts Ready: {drafts}                                              ║
║                                                                ║
║ ✅ Automation Complete                                           ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    print("=" * 60)
    print(f"🤖 DAILY AUTOMATION COMPLETED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main()