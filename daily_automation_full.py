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
    """Send batch of emails.

    Uses outreach.py's gmail_send(), which is the PROVEN, VERIFIED sender:
    it discards stale compose dialogs, scopes reads to its own dialog
    (data-hsn-compose), and verifies the send landed before returning "sent".

    The old inline send_email_cdp() below returned True UNCONDITIONALLY, so
    every "Sent x/50" line was fiction: on 2026-10-31 it logged 50 sends
    while Gmail's Sent folder contained ZERO of those emails (they died as
    drafts / never sent). Only mark a lead SENT when the sender confirms.
    """
    print(f"📧 Sending emails (max {max_emails})...")

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

    import outreach
    sent = 0
    failed = 0
    for to_email, club_name in pending:
        try:
            subject = f'Custom gear for {club_name} -- factory-direct pricing'
            body = f'''Hi {club_name.split()[0] if club_name else 'Team'},

Saw your club online -- impressive program. We are HSN Warrior Apparels, a custom fightwear manufacturer (since 2011).

We make custom gear with your logo, colors, and specs -- direct from our factory at club pricing (10-piece minimum).

Same-day quote with mockup. Just reply with your logo/colors & quantities.

-- HSN Warrior Apparels
+92 337 3336381 | hsnwarriorapparel@gmail.com
https://hsnwarriorapparels.vercel.app'''

            # gmail_send returns a STRING ('sent', 'recipient-not-registered', ...)
            res = outreach.gmail_send(to_email, subject, body)
            ok = isinstance(res, str) and res.strip().lower() == 'sent'
            if not isinstance(res, str):
                ok = bool(isinstance(res, dict) and res.get('ok'))

            if ok:
                # Update tracker
                update_tracker_email(to_email, 'SENT')
                sent += 1
                print(f"✅ Sent {sent}/{len(pending)}: {to_email}")
            else:
                failed += 1
                print(f"❌ Failed {to_email}: {res}")
                # Do NOT mark SENT. Leave READY_TO_SEND so it can be retried,
                # but remember the attempt so the next run skips it.
                update_tracker_email_failed(to_email, str(res)[:120])
        except Exception as e:
            failed += 1
            print(f"❌ Failed {to_email}: {e}")
            try:
                update_tracker_email_failed(to_email, str(e)[:120])
            except Exception:
                pass
        await asyncio.sleep(12)

    print(f"📧 Email batch done: {sent} sent, {failed} failed (of {len(pending)} attempted)")
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


def update_tracker_email_failed(email, reason):
    """Record a FAILED send without marking it SENT.

    The lead stays out of the READY_TO_SEND queue (so a retry does not
    re-hammer a dead address) but is clearly not counted as sent.
    """
    rows = []
    with open(TRACKER_FILE, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
    if len(rows) < 2:
        return
    changed = False
    for row in rows[1:]:
        if len(row) > 19 and row[4] == email and row[11] != 'SENT':
            row[11] = 'FAILED'
            row[12] = datetime.now().strftime('%Y-%m-%d')
            row[19] = f'FAILED: {reason}'[:200]
            changed = True
            break
    if not changed:
        return
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
    # timeout=1800 was too short: a 2-city run needs ~40 min (measured 2198s-4194s),
    # so the scrape was killed mid-flight every day BEFORE append_leads() ran --
    # the engine jobs finished "ok" but leads.csv got 0 new rows.
    # Use 5400s (90 min) and the PINNED interpreter (a bare `python3` can resolve to
    # an interpreter without openpyxl, breaking the Excel rebuild).
    print("\n📍 STEP 1: Google Maps Scraping")
    run_cmd("/home/ubuntu/.hermes/tools/python-3.14.7+20260901-linux-arm64/bin/python3 "
            "/home/ubuntu/gmaps_daily_scrape.py", timeout=5400)
    
    # Step 2: Clean and enrich
    print("\n🧹 STEP 2: Clean & Enrich Leads")
    run_cmd("python3 process_leads.py", timeout=300)

    # STEPS 3-5 DISABLED (2026-11-02): this path sent 50 emails on 2026-11-02
    # WITHOUT the QA pipeline, and 46 of them went to junk telemetry addresses
    # (sentry.wixpress.com / sentry.io) because the tracker rows were built by
    # splitting a raw comma-joined scrape cell into one row per address. It also
    # wrote "Hi <name>," greeting copy (banned by spam-word-checker) and
    # re-sent 2 leads already emailed on 2026-10-29. The real send path is the
    # dayNN wave chain (site-verify -> QA -> wave -> send) which enforces the
    # 100/day quota, the per-domain cap and the copy rules. This path now only
    # harvests leads; it never sends. Re-enable only with the QA chain in front.
    print("\n📧 STEP 3: email sends - DISABLED (handled by the dayNN wave chain)")
    sent_email = 0
    print("\n📱 STEP 4: IG DMs - DISABLED (handled by the dayNN IG pass)")
    sent_ig = 0
    print("\n💬 STEP 5: WhatsApp - DISABLED (handled by the dayNN WA phase)")
    sent_wa = 0
    
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