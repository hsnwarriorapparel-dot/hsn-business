#!/usr/bin/env python3
"""
Complete Daily Automation - Runs everything end-to-end
1. Scrape Google Maps
2. Clean & enrich leads
3. Send emails via Gmail CDP
4. Send IG DMs via Instagram CDP
5. Send WhatsApp via CDP
6. Update tracker
7. Git backup
"""

import asyncio
import websockets
import json
import requests
import csv
import subprocess
from datetime import datetime
from pathlib import Path

CDP_URL = "http://localhost:9222"
TRACKER_FILE = Path("/home/ubuntu/gmaps-output/outreach_tracker.csv")
DRAFTS_DIR = Path("/home/ubuntu/gmaps-output/drafts")

def run_cmd(cmd, cwd="/home/ubuntu", timeout=600):
    """Run shell command"""
    print(f"🔧 {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        if result.stdout:
            print(result.stdout[-1000:])
        if result.stderr:
            print(f"STDERR: {result.stderr[-500:]}")
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, "", str(e)

async def get_tabs():
    """Get all CDP tabs"""
    resp = requests.get(f"{CDP_URL}/json/list")
    return resp.json()

async def find_tab(pages, url_contains, tab_type="page"):
    """Find tab by URL"""
    for page in pages:
        if url_contains in page.get('url', '') and page.get('type') == tab_type:
            return page
    return None

async def cdp_click(ws, x, y):
    """Click at coordinates via CDP"""
    await ws.send(json.dumps({
        'method': 'Input.dispatchMouseEvent',
        'params': {'type': 'mousePressed', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1}
    }))
    while True:
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data:
            break
    
    await ws.send(json.dumps({
        'method': 'Input.dispatchMouseEvent',
        'params': {'type': 'mouseReleased', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1}
    }))
    while True:
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data:
            break

async def cdp_eval(ws, expr, cmd_id):
    """Evaluate expression via CDP"""
    await ws.send(json.dumps({
        'id': cmd_id,
        'method': 'Runtime.evaluate',
        'params': {'expression': expr, 'awaitPromise': True, 'returnByValue': True}
    }))
    while True:
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == cmd_id:
            return data

async def send_email_cdp(gmail_tab, to_email, subject, body):
    """Send single email via Gmail CDP"""
    ws_url = gmail_tab['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url) as ws:
        # Enable Runtime
        await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
        while True:
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 1:
                break
        
        await asyncio.sleep(1)
        
        # Compose
        await cdp_eval(ws, '''
        (function() {
            var btn = document.querySelector('[gh="cm"]');
            if (btn) { btn.click(); return 'clicked'; }
            btn = document.querySelector('[aria-label*="Compose"]');
            if (btn) { btn.click(); return 'clicked2'; }
            return 'not found';
        })()
        ''', 2)
        await asyncio.sleep(1.5)
        
        # To
        await cdp_eval(ws, f'''
        (function() {{
            var toInput = document.querySelector('[name="to"]') || document.querySelector('textarea[aria-label="To"]');
            if (toInput) {{ toInput.focus(); toInput.value = '{to_email}'; toInput.dispatchEvent(new Event('input', {{bubbles: true}})); toInput.dispatchEvent(new KeyboardEvent('keydown', {{key: 'Enter', bubbles: true}})); return 'filled'; }}
            return 'not found';
        }})()
        ''', 3)
        await asyncio.sleep(1)
        
        # Subject
        await cdp_eval(ws, f'''
        (function() {{
            var s = document.querySelector('[name="subjectbox"]');
            if (s) {{ s.focus(); s.value = '{subject.replace("'", "\\'")}'; s.dispatchEvent(new Event('input', {{bubbles: true}})); return 'filled'; }}
            return 'not found';
        }})()
        ''', 4)
        await asyncio.sleep(1)
        
        # Body
        body_js = body.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"').replace("'", "\\'")
        await cdp_eval(ws, f'''
        (function() {{
            var b = document.querySelector('[aria-label="Message Body"]') || document.querySelector('.Am.Al.editable');
            if (b) {{ b.focus(); b.innerText = '{body_js}'; b.dispatchEvent(new Event('input', {{bubbles: true}})); return 'filled'; }}
            return 'not found';
        }})()
        ''', 5)
        await asyncio.sleep(1)
        
        # Send
        await cdp_eval(ws, '''
        (function() {
            var btn = document.querySelector('[aria-label*="Send"]');
            if (btn) { btn.click(); return 'sent'; }
            return 'not found';
        })()
        ''', 6)
        await asyncio.sleep(3)
        
        return True

async def send_emails_batch(max_emails=50):
    """Send batch of emails"""
    print(f"📧 Sending emails (max {max_emails})...")
    
    pages = await get_tabs()
    gmail_tab = await find_tab(pages, 'mail.google.com')
    if not gmail_tab:
        print("❌ Gmail tab not found")
        return 0
    
    # Read pending emails from tracker
    pending = []
    with open(TRACKER_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Email Sent'] == 'READY_TO_SEND':
                pending.append((row['Email'], row['Club Name']))
                if len(pending) >= max_emails:
                    break
    
    print(f"Found {len(pending)} pending emails")
    
    sent = 0
    for to_email, club_name in pending:
        try:
            subject = f'Custom gear for {club_name} -- factory-direct pricing'
            body = f'''Hi {club_name.split()[0] if club_name else 'Team'},

Saw your club online -- impressive program. We are HSN Warrior Apparels, a custom fightwear manufacturer (since 2011).

We make custom gear with your logo, colors, and specs -- direct from our factory at club pricing (10-piece minimum).

Same-day quote with mockup. Just reply with your logo/colors & quantities.

-- HSN Warrior Apparels
+92 337 3336381 | hsnwarriorapparels@gmail.com
https://hsnwarriorapparels.vercel.app'''
            
            await send_email_cdp(gmail_tab, to_email, subject, body)
            
            # Update tracker
            update_tracker_email(to_email, 'SENT')
            sent += 1
            print(f"✅ Sent {sent}/{len(pending)}: {to_email}")
            
            await asyncio.sleep(5)  # Rate limit
            
        except Exception as e:
            print(f"❌ Failed {to_email}: {e}")
            continue
    
    return sent

async def send_ig_dms_batch(max_dms=20):
    """Send batch of IG DMs via profile navigation"""
    print(f"📱 Sending IG DMs (max {max_dms})...")
    
    pages = await get_tabs()
    ig_tab = await find_tab(pages, 'instagram.com')
    if not ig_tab:
        print("❌ Instagram tab not found")
        return 0
    
    ws_url = ig_tab['webSocketDebuggerUrl']
    
    # Read pending IG DMs from tracker
    pending = []
    with open(TRACKER_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['IG DM Sent'] == 'PENDING':
                # Try to get Instagram username from club name or website
                club = row['Club Name']
                website = row.get('Website', '')
                # For now, use club name as username guess
                username = club.lower().replace(' ', '').replace('.', '').replace(',', '').replace('&', '').replace('-', '')
                pending.append((row['Email'], club, username))
                if len(pending) >= max_dms:
                    break
    
    print(f"Found {len(pending)} pending IG DMs")
    
    sent = 0
    async with websockets.connect(ws_url) as ws:
        # Enable Runtime
        await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
        while True:
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 1:
                break
        
        for email, club, username in pending:
            try:
                print(f"\n📤 DM to {club} (@{username})...")
                
                # Navigate to profile
                await ws.send(json.dumps({
                    'method': 'Page.navigate',
                    'params': {'url': f'https://www.instagram.com/{username}/'}
                }))
                while True:
                    resp = await ws.recv()
                    data = json.loads(resp)
                    if 'id' in data:
                        break
                
                await asyncio.sleep(5)
                
                # Find and click Message button (profile page coords may vary)
                # Try standard position first
                await cdp_click(ws, 843, 244)
                await asyncio.sleep(3)
                
                # Type message
                message = f'''Hi! Saw your club online -- impressive program.

We are HSN Warrior Apparels, a custom fightwear manufacturer (since 2011). We make custom gear with your logo, colors & specs -- factory-direct, 10-piece minimum.

Same-day quote + mockup. Just reply with your logo/colors & quantities.

-- HSN Warrior Apparels
+92 337 3336381 | hsnwarriorapparels@gmail.com
hsnwarriorapparels.vercel.app'''
                
                await cdp_eval(ws, f'''
                (function() {{
                    var inp = document.querySelector('textarea[placeholder*="Message"]') || 
                              document.querySelector('div[aria-label*="Message"]') ||
                              document.querySelector('[role="textbox"]');
                    if (inp) {{ inp.focus(); inp.innerText = `{message.replace("`", "\\`")}`; inp.dispatchEvent(new Event('input', {{bubbles: true}})); return 'typed'; }}
                    return 'not found';
                }})()
                ''', 10)
                await asyncio.sleep(1)
                
                # Click Send (profile DM composer position)
                await cdp_click(ws, 1142, 725)
                await asyncio.sleep(2)
                
                # Update tracker
                update_tracker_ig(email, 'SENT')
                sent += 1
                print(f"✅ Sent DM {sent}/{len(pending)}: {club}")
                
                await asyncio.sleep(8)  # Rate limit
                
            except Exception as e:
                print(f"❌ Failed {club}: {e}")
                continue
    
    return sent

async def send_whatsapp_batch(max_wa=10):
    """Send batch of WhatsApp messages"""
    print(f"💬 Sending WhatsApp (max {max_wa})...")
    
    pages = await get_tabs()
    wa_tab = await find_tab(pages, 'web.whatsapp.com')
    if not wa_tab:
        print("❌ WhatsApp tab not found")
        return 0
    
    ws_url = wa_tab['webSocketDebuggerUrl']
    
    # Read pending WhatsApp from tracker
    pending = []
    with open(TRACKER_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['WA Sent'] == 'PENDING' and row.get('Phone'):
                pending.append((row['Phone'], row['Email'], row['Club Name']))
                if len(pending) >= max_wa:
                    break
    
    print(f"Found {len(pending)} pending WhatsApp")
    
    sent = 0
    async with websockets.connect(ws_url) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
        while True:
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 1:
                break
        
        for phone, email, club in pending:
            try:
                print(f"\n📤 WhatsApp to {club} ({phone})...")
                
                # Search for contact
                await cdp_eval(ws, f'''
                (function() {{
                    var searchBox = document.querySelector('[data-testid="chat-list-search"]') ||
                                   document.querySelector('[aria-label="Search"]') ||
                                   document.querySelector('input[type="text"]');
                    if (searchBox) {{
                        searchBox.focus();
                        searchBox.value = '{phone}';
                        searchBox.dispatchEvent(new Event('input', {{bubbles: true}}));
                        return 'searched';
                    }}
                    return 'not found';
                }})()
                ''', 10)
                await asyncio.sleep(3)
                
                # Click first result (approximate position)
                await cdp_click(ws, 400, 300)
                await asyncio.sleep(2)
                
                # Type message
                message = f'''Hi! Saw your club online -- impressive program.

We are HSN Warrior Apparels, a custom fightwear manufacturer (since 2011). We make custom gear with your logo, colors & specs -- factory-direct, 10-piece minimum.

Same-day quote + mockup. Just reply with your logo/colors & quantities.

-- HSN Warrior Apparels
+92 337 3336381 | hsnwarriorapparels@gmail.com
hsnwarriorapparels.vercel.app'''
                
                await cdp_eval(ws, f'''
                (function() {{
                    var inp = document.querySelector('[data-testid="conversation-compose-box-input"]') ||
                               document.querySelector('[aria-label="Type a message"]') ||
                               document.querySelector('div[contenteditable="true"][data-tab="10"]');
                    if (inp) {{ inp.focus(); inp.innerText = `{message.replace("`", "\\`")}`; inp.dispatchEvent(new Event('input', {{bubbles: true}})); return 'typed'; }}
                    return 'not found';
                }})()
                ''', 20)
                await asyncio.sleep(1)
                
                # Click Send
                await cdp_eval(ws, '''
                (function() {
                    var btn = document.querySelector('[data-testid="compose-btn-send"]') ||
                               document.querySelector('[aria-label="Send"]') ||
                               document.querySelector('span[data-icon="send"]');
                    if (btn) { btn.click(); return 'sent'; }
                    return 'not found';
                })()
                ''', 30)
                await asyncio.sleep(2)
                
                # Update tracker
                update_tracker_wa(email, 'SENT')
                sent += 1
                print(f"✅ Sent WA {sent}/{len(pending)}: {club}")
                
                await asyncio.sleep(10)  # Rate limit
                
            except Exception as e:
                print(f"❌ Failed {club}: {e}")
                continue
    
    return sent

def update_tracker_email(email, status):
    """Update email status in tracker"""
    rows = []
    with open(TRACKER_FILE, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    for row in rows[1:]:
        if row[4] == email:
            row[11] = status
            row[12] = datetime.now().strftime('%Y-%m-%d')
            break
    
    with open(TRACKER_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def update_tracker_ig(email, status):
    """Update IG DM status in tracker"""
    rows = []
    with open(TRACKER_FILE, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    for row in rows[1:]:
        if row[4] == email:
            row[13] = status
            row[14] = datetime.now().strftime('%Y-%m-%d')
            break
    
    with open(TRACKER_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def update_tracker_wa(email, status):
    """Update WhatsApp status in tracker"""
    rows = []
    with open(TRACKER_FILE, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    for row in rows[1:]:
        if row[4] == email:
            row[15] = status
            row[16] = datetime.now().strftime('%Y-%m-%d')
            break
    
    with open(TRACKER_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def generate_report():
    """Generate summary report"""
    if not TRACKER_FILE.exists():
        return
    
    sent_email = sent_ig = sent_wa = total = 0
    with open(TRACKER_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            if row.get('Email Sent') == 'SENT':
                sent_email += 1
            if row.get('IG DM Sent') == 'SENT':
                sent_ig += 1
            if row.get('WA Sent') == 'SENT':
                sent_wa += 1
    
    drafts = len(list(DRAFTS_DIR.glob("*.eml"))) if DRAFTS_DIR.exists() else 0
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    DAILY AUTOMATION REPORT                     ║
╠══════════════════════════════════════════════════════════════╣
║ Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                                    ║
║                                                                ║
║ 📧 Emails Sent: {sent_email}                                               ║
║ 📱 IG DMs Sent: {sent_ig}                                                ║
║ 💬 WhatsApp Sent: {sent_wa}                                             ║
║ 📊 Total Tracker Rows: {total}                                           ║
║ 📝 Drafts Ready: {drafts}                                              ║
║                                                                ║
║ ✅ Automation Complete                                           ║
╚══════════════════════════════════════════════════════════════╝
    """)

async def main():
    print("=" * 60)
    print(f"🤖 DAILY AUTOMATION STARTED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Step 1: Scrape new leads
    print("\n📍 STEP 1: Google Maps Scraping")
    run_cmd("python3 gmaps_daily_scrape.py", timeout=1800)
    
    # Step 2: Clean and enrich
    print("\n🧹 STEP 2: Clean & Enrich Leads")
    run_cmd("python3 process_leads.py", timeout=300)
    
    # Step 3: Send emails
    print("\n📧 STEP 3: Send Emails")
    sent_email = await send_emails_batch(50)
    
    # Step 4: Send IG DMs
    print("\n📱 STEP 4: Send IG DMs")
    sent_ig = await send_ig_dms_batch(20)
    
    # Step 5: Send WhatsApp
    print("\n💬 STEP 5: Send WhatsApp")
    sent_wa = await send_whatsapp_batch(10)
    
    # Step 6: Git backup
    print("\n💾 STEP 6: Git Backup")
    run_cmd("git add -A && git commit -m 'Daily automation' && git push", timeout=120)
    
    # Step 7: Report
    print("\n📊 STEP 7: Report")
    generate_report()
    
    print("=" * 60)
    print(f"🤖 DAILY AUTOMATION COMPLETED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())