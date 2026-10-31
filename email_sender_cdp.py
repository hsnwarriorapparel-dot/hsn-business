#!/usr/bin/env python3
"""
Email Sender using CDP - Uses existing logged-in Gmail session
Sends .eml drafts from /home/ubuntu/gmaps-output/drafts/
"""

import asyncio
import json
import os
import csv
import re
from datetime import datetime
from pathlib import Path
import websockets

DRAFTS_DIR = Path("/home/ubuntu/gmaps-output/drafts")
TRACKER_FILE = Path("/home/ubuntu/gmaps-output/outreach_tracker.csv")
CDP_URL = "http://localhost:9222"

async def get_gmail_tab():
    """Find the Gmail tab in CDP"""
    import requests
    resp = requests.get(f"{CDP_URL}/json/list")
    pages = resp.json()
    
    for page in pages:
        url = page.get('url', '')
        if 'mail.google.com' in url and page.get('type') == 'page':
            return page
    return None

async def send_cdp_command(ws, cmd_id, expression):
    """Send CDP command and wait for result"""
    await ws.send(json.dumps({"id": cmd_id, "method": "Runtime.evaluate", "params": {"expression": expression, "awaitPromise": True, "returnByValue": True}}))
    while True:
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == cmd_id:
            return data
        elif 'method' in data:
            pass  # Ignore events

async def send_email_via_cdp(gmail_tab, to_email, subject, body):
    """Send email using CDP by interacting with Gmail compose"""
    ws_url = gmail_tab['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url) as ws:
        # Enable Runtime
        await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
        while True:
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 1:
                break
        
        # Click "Compose" button
        compose_click = '''
        (function() {
            var btn = document.querySelector('[gh="cm"]');
            if (btn) { btn.click(); return 'clicked gh=cm'; }
            btn = document.querySelector('[aria-label*="Compose"]');
            if (btn) { btn.click(); return 'clicked aria-label'; }
            btn = document.querySelector('.T-I.T-I-KE.L3');
            if (btn) { btn.click(); return 'clicked T-I-KE'; }
            return 'compose button not found';
        })()
        '''
        result = await send_cdp_command(ws, 2, compose_click)
        print(f"Compose: {result.get('result', {}).get('result', {}).get('value', 'unknown')}")
        await asyncio.sleep(1.5)
        
        # Fill To field
        fill_to = f'''
        (function() {{
            var toInput = document.querySelector('[name="to"]') ||
                         document.querySelector('textarea[aria-label="To"]') ||
                         document.querySelector('[data-tooltip="Add recipients"]');
            if (toInput) {{
                toInput.focus();
                toInput.value = '{to_email}';
                toInput.dispatchEvent(new Event('input', {{bubbles: true}}));
                toInput.dispatchEvent(new Event('change', {{bubbles: true}}));
                var event = new KeyboardEvent('keydown', {{key: 'Enter', bubbles: true}});
                toInput.dispatchEvent(event);
                return 'filled to';
            }}
            return 'to input not found';
        }})()
        '''
        result = await send_cdp_command(ws, 3, fill_to)
        print(f"Fill To: {result.get('result', {}).get('result', {}).get('value', 'unknown')}")
        await asyncio.sleep(1)
        
        # Fill Subject
        fill_subject = f'''
        (function() {{
            var subjInput = document.querySelector('[name="subjectbox"]') ||
                           document.querySelector('input[aria-label="Subject"]');
            if (subjInput) {{
                subjInput.focus();
                subjInput.value = '{subject.replace("'", "\\'")}';
                subjInput.dispatchEvent(new Event('input', {{bubbles: true}}));
                subjInput.dispatchEvent(new Event('change', {{bubbles: true}}));
                return 'filled subject';
            }}
            return 'subject input not found';
        }})()
        '''
        result = await send_cdp_command(ws, 4, fill_subject)
        print(f"Fill Subject: {result.get('result', {}).get('result', {}).get('value', 'unknown')}")
        await asyncio.sleep(1)
        
        # Fill Body
        fill_body = f'''
        (function() {{
            var bodyDiv = document.querySelector('[aria-label="Message Body"]') ||
                         document.querySelector('.Am.Al.editable') ||
                         document.querySelector('[role="textbox"][g_editable="true"]');
            if (bodyDiv) {{
                bodyDiv.focus();
                bodyDiv.innerText = `{body.replace("`", "\\`").replace("${", "\\${")}`;
                bodyDiv.dispatchEvent(new Event('input', {{bubbles: true}}));
                return 'filled body';
            }}
            return 'body input not found';
        }})()
        '''
        result = await send_cdp_command(ws, 5, fill_body)
        print(f"Fill Body: {result.get('result', {}).get('result', {}).get('value', 'unknown')}")
        await asyncio.sleep(1)
        
        # Click Send
        click_send = '''
        (function() {
            var sendBtn = document.querySelector('[aria-label*="Send"]') ||
                         document.querySelector('.T-I.J-J5-Ji.aoO.v7.T-I-atl.L3') ||
                         document.querySelector('[data-tooltip="Send"]');
            if (sendBtn) {
                sendBtn.click();
                return 'clicked send';
            }
            return 'send button not found';
        })()
        '''
        result = await send_cdp_command(ws, 6, click_send)
        print(f"Click Send: {result.get('result', {}).get('result', {}).get('value', 'unknown')}")
        await asyncio.sleep(3)
        
        return True

def parse_eml(filepath):
    """Parse .eml file to extract to, subject, body"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Parse headers
    lines = content.split('\n')
    to_email = ""
    subject = ""
    body_start = 0
    
    for i, line in enumerate(lines):
        if line.lower().startswith('to:'):
            to_email = line[3:].strip()
        elif line.lower().startswith('subject:'):
            subject = line[8:].strip()
        elif line == '' and body_start == 0:
            body_start = i + 1
            break
    
    body = '\n'.join(lines[body_start:]) if body_start > 0 else ''
    return to_email, subject, body

def update_tracker(email, status, date_col):
    """Update outreach tracker"""
    rows = []
    with open(TRACKER_FILE, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    for row in rows[1:]:
        if row[4] == email:
            row[11] = status  # Email Sent
            row[12] = date_col  # Email Date
            break
    
    with open(TRACKER_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

async def main():
    print("🚀 Starting Gmail CDP Automation...")
    
    # Get Gmail tab
    gmail_tab = await get_gmail_tab()
    if not gmail_tab:
        print("❌ Gmail tab not found!")
        return
    
    print(f"✅ Found Gmail tab: {gmail_tab['title']}")
    
    # Get all drafts
    drafts = list(DRAFTS_DIR.glob("*.eml"))
    print(f"📧 Found {len(drafts)} email drafts")
    
    # Process each draft
    sent_count = 0
    for draft_file in drafts:
        if sent_count >= 100:  # Gmail daily limit
            print("⚠️ Reached daily limit (100)")
            break
            
        try:
            to_email, subject, body = parse_eml(draft_file)
            if not to_email or not subject:
                print(f"⚠️ Skipping {draft_file.name}: missing to/subject")
                continue
            
            print(f"\n📤 Sending to: {to_email}")
            print(f"   Subject: {subject}")
            
            await send_email_via_cdp(gmail_tab, to_email, subject, body)
            
            # Update tracker
            today = datetime.now().strftime('%Y-%m-%d')
            update_tracker(to_email, 'SENT', today)
            
            sent_count += 1
            print(f"✅ Sent #{sent_count}")
            
            # Rate limiting - human-like delays
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"❌ Error sending {draft_file.name}: {e}")
            continue
    
    print(f"\n✅ Done! Sent {sent_count} emails")

if __name__ == "__main__":
    asyncio.run(main())