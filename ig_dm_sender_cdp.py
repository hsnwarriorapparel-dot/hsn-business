#!/usr/bin/env python3
"""
Instagram DM Sender using CDP - Uses existing logged-in Instagram session
Sends DMs from /home/ubuntu/gmaps-output/ig_dm_drafts.txt
"""

import asyncio
import json
import os
import csv
import re
from datetime import datetime
from pathlib import Path
import websockets
import requests

IG_DM_FILE = Path("/home/ubuntu/gmaps-output/ig_dm_drafts.txt")
TRACKER_FILE = Path("/home/ubuntu/gmaps-output/outreach_tracker.csv")
CDP_URL = "http://localhost:9222"

async def get_instagram_tabs():
    """Find Instagram tabs in CDP"""
    resp = requests.get(f"{CDP_URL}/json/list")
    pages = resp.json()
    
    ig_tabs = []
    for page in pages:
        url = page.get('url', '')
        if 'instagram.com' in url and page.get('type') == 'page':
            ig_tabs.append(page)
    return ig_tabs

async def send_dm_via_cdp(ig_tab, username, message):
    """Send DM via Instagram web using CDP"""
    ws_url = ig_tab['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url) as ws:
        # Enable Runtime
        await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
        await ws.recv()
        
        # Navigate to DM inbox if not there
        current_url = ig_tab.get('url', '')
        if 'direct/inbox' not in current_url:
            navigate = f"""
            (() => {{
                window.location.href = 'https://www.instagram.com/direct/inbox/';
                return true;
            }})()
            """
            await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": navigate, "awaitPromise": True}}))
            await ws.recv()
            await asyncio.sleep(3)
        
        # Search for user
        search_user = f"""
        (() => {{
            // Click new message button
            const newMsgBtn = document.querySelector('[aria-label="New message"]') ||
                             document.querySelector('svg[aria-label="New message"]') ||
                             document.querySelector('button:has(svg[aria-label="New message"])');
            if (newMsgBtn) {{
                newMsgBtn.click();
                return 'clicked_new_message';
            }}
            return 'new_msg_not_found';
        }})()
        """
        await ws.send(json.dumps({"id": 3, "method": "Runtime.evaluate", "params": {"expression": search_user, "awaitPromise": True}}))
        result = await ws.recv()
        print(f"New message: {result}")
        await asyncio.sleep(2)
        
        # Type username in search
        type_username = f"""
        (() => {{
            const searchInput = document.querySelector('input[placeholder*="Search"]') ||
                               document.querySelector('input[aria-label*="Search"]') ||
                               document.querySelector('input[type="text"]');
            if (searchInput) {{
                searchInput.focus();
                searchInput.value = '{username}';
                searchInput.dispatchEvent(new Event('input', {{bubbles: true}}));
                return true;
            }}
            return false;
        }})()
        """
        await ws.send(json.dumps({"id": 4, "method": "Runtime.evaluate", "params": {"expression": type_username, "awaitPromise": True}}))
        result = await ws.recv()
        print(f"Type username: {result}")
        await asyncio.sleep(3)
        
        # Click on user result
        click_user = f"""
        (() => {{
            const userElements = document.querySelectorAll('button, div[role="button"], a');
            for (const el of userElements) {{
                if (el.textContent.includes('{username}')) {{
                    el.click();
                    return true;
                }}
            }}
            return false;
        }})()
        """
        await ws.send(json.dumps({"id": 5, "method": "Runtime.evaluate", "params": {"expression": click_user, "awaitPromise": True}}))
        result = await ws.recv()
        print(f"Click user: {result}")
        await asyncio.sleep(2)
        
        # Click "Next" or "Chat"
        click_next = """
        (() => {
            const nextBtn = document.querySelector('button:contains("Next")') ||
                           document.querySelector('div[role="button"]:contains("Next")') ||
                           document.querySelector('button:contains("Chat")') ||
                           document.querySelector('div[role="button"]:contains("Chat")');
            if (nextBtn) {
                nextBtn.click();
                return true;
            }
            return false;
        })()
        """
        await ws.send(json.dumps({"id": 6, "method": "Runtime.evaluate", "params": {"expression": click_next, "awaitPromise": True}}))
        result = await ws.recv()
        print(f"Click next: {result}")
        await asyncio.sleep(2)
        
        # Type message
        type_message = f"""
        (() => {{
            const msgInput = document.querySelector('textarea[placeholder*="Message"]') ||
                            document.querySelector('div[aria-label*="Message"]') ||
                            document.querySelector('[role="textbox"]');
            if (msgInput) {{
                msgInput.focus();
                msgInput.innerText = `{message.replace("`", "\\`").replace("${", "\\${")}`;
                msgInput.dispatchEvent(new Event('input', {{bubbles: true}}));
                return true;
            }}
            return false;
        }})()
        """
        await ws.send(json.dumps({"id": 7, "method": "Runtime.evaluate", "params": {"expression": type_message, "awaitPromise": True}}))
        result = await ws.recv()
        print(f"Type message: {result}")
        await asyncio.sleep(1)
        
        # Click Send
        click_send = """
        (() => {
            const sendBtn = document.querySelector('button:contains("Send")') ||
                           document.querySelector('div[role="button"]:contains("Send")') ||
                           document.querySelector('[aria-label="Send"]');
            if (sendBtn) {
                sendBtn.click();
                return true;
            }
            return false;
        })()
        """
        await ws.send(json.dumps({"id": 8, "method": "Runtime.evaluate", "params": {"expression": click_send, "awaitPromise": True}}))
        result = await ws.recv()
        print(f"Click send: {result}")
        await asyncio.sleep(2)
        
        return True

def parse_ig_drafts(filepath):
    """Parse IG DM drafts file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Split by club sections
    sections = content.split('CLUB: ')[1:]  # First is empty
    drafts = []
    
    for section in sections:
        lines = section.strip().split('\n')
        club_name = lines[0].strip()
        
        # Find email line
        email = ""
        for line in lines:
            if line.startswith('EMAIL:'):
                email = line[6:].strip()
                break
        
        # Find DM message
        dm_start = -1
        for i, line in enumerate(lines):
            if line.startswith('DM MESSAGE:'):
                dm_start = i
                break
        
        if dm_start >= 0:
            dm_message = '\n'.join(lines[dm_start+1:]).strip()
            # Remove trailing separator
            dm_message = dm_message.split('\n-\n-\n-\n-\n-')[0].strip()
        else:
            dm_message = ""
        
        if club_name and dm_message:
            drafts.append({
                'club': club_name,
                'email': email,
                'message': dm_message
            })
    
    return drafts

def update_tracker_ig(email, status, date_col):
    """Update outreach tracker for IG DM"""
    rows = []
    with open(TRACKER_FILE, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    for row in rows[1:]:
        if row[4] == email:
            row[13] = status  # IG DM Sent
            row[14] = date_col  # IG DM Date
            break
    
    with open(TRACKER_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

async def main():
    print("🚀 Starting Instagram DM CDP Automation...")
    
    # Get Instagram tabs
    ig_tabs = await get_instagram_tabs()
    if not ig_tabs:
        print("❌ Instagram tab not found!")
        return
    
    # Use the direct inbox tab
    ig_tab = None
    for tab in ig_tabs:
        if 'direct/inbox' in tab.get('url', ''):
            ig_tab = tab
            break
    
    if not ig_tab:
        ig_tab = ig_tabs[0]
    
    print(f"✅ Found Instagram tab: {ig_tab['title']}")
    
    # Parse drafts
    drafts = parse_ig_drafts(IG_DM_FILE)
    print(f"📱 Found {len(drafts)} IG DM drafts")
    
    # Process each draft
    sent_count = 0
    for draft in drafts:
        if sent_count >= 50:  # Daily limit
            print("⚠️ Reached daily limit (50)")
            break
            
        try:
            club = draft['club']
            email = draft['email']
            message = draft['message']
            
            # Extract username from club name or use first word
            username = club.split()[0].lower().replace('.', '').replace(',', '')
            
            print(f"\n📤 Sending DM to: {club} ({username})")
            print(f"   Email: {email}")
            
            await send_dm_via_cdp(ig_tab, username, message)
            
            # Update tracker
            today = datetime.now().strftime('%Y-%m-%d')
            update_tracker_ig(email, 'SENT', today)
            
            sent_count += 1
            print(f"✅ Sent DM #{sent_count}")
            
            # Rate limiting
            await asyncio.sleep(8)
            
        except Exception as e:
            print(f"❌ Error sending DM to {draft['club']}: {e}")
            continue
    
    print(f"\n✅ Done! Sent {sent_count} IG DMs")

if __name__ == "__main__":
    asyncio.run(main())