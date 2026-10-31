#!/usr/bin/env python3
"""
WhatsApp Sender using CDP - Uses existing logged-in WhatsApp Web session
Sends messages from outreach tracker
"""

import asyncio
import json
import csv
from datetime import datetime
from pathlib import Path
import websockets
import requests

TRACKER_FILE = Path("/home/ubuntu/gmaps-output/outreach_tracker.csv")
CDP_URL = "http://localhost:9222"

async def get_whatsapp_tab():
    """Find WhatsApp Web tab in CDP"""
    resp = requests.get(f"{CDP_URL}/json/list")
    pages = resp.json()
    
    for page in pages:
        url = page.get('url', '')
        if 'web.whatsapp.com' in url and page.get('type') == 'page':
            return page
    return None

async def send_wa_via_cdp(wa_tab, phone, message):
    """Send WhatsApp message via CDP"""
    ws_url = wa_tab['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url) as ws:
        # Enable Runtime
        await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
        await ws.recv()
        
        # Search for contact
        search_contact = f"""
        (() => {{
            const searchBox = document.querySelector('[data-testid="chat-list-search"]') ||
                             document.querySelector('[aria-label="Search"]') ||
                             document.querySelector('input[type="text"]');
            if (searchBox) {{
                searchBox.focus();
                searchBox.value = '{phone}';
                searchBox.dispatchEvent(new Event('input', {{bubbles: true}}));
                return true;
            }}
            return false;
        }})()
        """
        await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": search_contact, "awaitPromise": True}}))
        result = await ws.recv()
        print(f"Search contact: {result}")
        await asyncio.sleep(3)
        
        # Click on contact
        click_contact = """
        (() => {
            const chatItems = document.querySelectorAll('[data-testid="chat-list-item"], div[role="listitem"]');
            for (const item of chatItems) {
                item.click();
                return true;
            }
            return false;
        })()
        """
        await ws.send(json.dumps({"id": 3, "method": "Runtime.evaluate", "params": {"expression": click_contact, "awaitPromise": True}}))
        result = await ws.recv()
        print(f"Click contact: {result}")
        await asyncio.sleep(2)
        
        # Type message
        type_message = f"""
        (() => {{
            const msgInput = document.querySelector('[data-testid="conversation-compose-box-input"]') ||
                            document.querySelector('[aria-label="Type a message"]') ||
                            document.querySelector('div[contenteditable="true"][data-tab="10"]');
            if (msgInput) {{
                msgInput.focus();
                msgInput.innerText = `{message.replace("`", "\\`").replace("${", "\\${")}`;
                msgInput.dispatchEvent(new Event('input', {{bubbles: true}}));
                return true;
            }}
            return false;
        }})()
        """
        await ws.send(json.dumps({"id": 4, "method": "Runtime.evaluate", "params": {"expression": type_message, "awaitPromise": True}}))
        result = await ws.recv()
        print(f"Type message: {result}")
        await asyncio.sleep(1)
        
        # Click Send
        click_send = """
        (() => {
            const sendBtn = document.querySelector('[data-testid="compose-btn-send"]') ||
                           document.querySelector('[aria-label="Send"]') ||
                           document.querySelector('span[data-icon="send"]');
            if (sendBtn) {
                sendBtn.click();
                return true;
            }
            return false;
        })()
        """
        await ws.send(json.dumps({"id": 5, "method": "Runtime.evaluate", "params": {"expression": click_send, "awaitPromise": True}}))
        result = await ws.recv()
        print(f"Click send: {result}")
        await asyncio.sleep(2)
        
        return True

def get_wa_contacts():
    """Get contacts from tracker that need WhatsApp"""
    contacts = []
    with open(TRACKER_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('WA Sent') == 'PENDING' and row.get('Phone'):
                contacts.append({
                    'phone': row['Phone'],
                    'email': row['Email'],
                    'club': row['Club Name']
                })
    return contacts

def update_tracker_wa(email, status, date_col):
    """Update outreach tracker for WhatsApp"""
    rows = []
    with open(TRACKER_FILE, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    for row in rows[1:]:
        if row[4] == email:
            row[15] = status  # WA Sent
            row[16] = date_col  # WA Date
            break
    
    with open(TRACKER_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

async def main():
    print("🚀 Starting WhatsApp CDP Automation...")
    
    # Get WhatsApp tab
    wa_tab = await get_whatsapp_tab()
    if not wa_tab:
        print("❌ WhatsApp tab not found!")
        return
    
    print(f"✅ Found WhatsApp tab: {wa_tab['title']}")
    
    # Get contacts
    contacts = get_wa_contacts()
    print(f"📱 Found {len(contacts)} contacts needing WhatsApp")
    
    # Process each contact
    sent_count = 0
    for contact in contacts:
        if sent_count >= 10:  # Daily limit for new number
            print("⚠️ Reached daily limit (10)")
            break
            
        try:
            phone = contact['phone']
            email = contact['email']
            club = contact['club']
            
            message = f"""Hi! Saw your club online — impressive program. 

We're HSN Warrior Apparels, a custom fightwear manufacturer (since 2011). We make custom gear with your logo, colors & specs — factory-direct, 10-piece minimum.

Same-day quote + mockup. Just reply with your logo/colors & quantities.

— HSN Warrior Apparels
+92 337 3336381 | hsnwarriorapparels@gmail.com
hsnwarriorapparels.vercel.app"""
            
            print(f"\n📤 Sending WhatsApp to: {club} ({phone})")
            
            await send_wa_via_cdp(wa_tab, phone, message)
            
            # Update tracker
            today = datetime.now().strftime('%Y-%m-%d')
            update_tracker_wa(email, 'SENT', today)
            
            sent_count += 1
            print(f"✅ Sent WhatsApp #{sent_count}")
            
            # Rate limiting
            await asyncio.sleep(10)
            
        except Exception as e:
            print(f"❌ Error sending WhatsApp to {contact['club']}: {e}")
            continue
    
    print(f"\n✅ Done! Sent {sent_count} WhatsApp messages")

if __name__ == "__main__":
    asyncio.run(main())