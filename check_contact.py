import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

# More business/gym profiles from the post comments
TARGET_PROFILES = [
    'martial_arts_manufacturer_',  # competitor but might have email
    'berlin.sportswear.co.',       # competitor
    'ssisales',                    # competitor/supplier
    'mehran_industry',             # competitor
    'jiujitsu__gi',                # might be shop/gym
    'bjjnotesapp',                 # app/business
    'goldpanelsport',              # already tried
    'phuketfightclub',             # already tried
]

async def check_contact_button(ws, profile):
    print(f'\n=== CHECKING @{profile} FOR CONTACT BUTTON ===')
    
    # Navigate to profile
    print(f'1. Navigating to /{profile}/...')
    await ws.send(json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': f'https://www.instagram.com/{profile}/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 1:
            break
    
    await asyncio.sleep(5)
    
    # Check for Contact button and email
    print('2. Checking for Contact button and emails...')
    expr = r'(function() { const allText = document.body.innerText; const emails = allText.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g); const contactBtns = []; document.querySelectorAll("button, div[role=\"button\"]").forEach(b => { const text = (b.innerText || "").toLowerCase(); if (text.includes("contact") || text.includes("email") || text.includes("kontakt")) contactBtns.push({text: b.innerText, class: b.className}); }); return JSON.stringify({emails: emails || [], contactBtns: contactBtns}); })()'
    await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            result = json.loads(data['result'].get('value', '{}'))
            print(f'   Emails: {result.get("emails", [])}')
            print(f'   Contact buttons: {result.get("contactBtns", [])}')
            break
    
    return result.get('emails', [])

async def main():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 0, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    all_emails = []
    for profile in TARGET_PROFILES:
        emails = await check_contact_button(ws, profile)
        all_emails.extend(emails)
        await asyncio.sleep(3)
    
    print('\n=== SUMMARY ===')
    print(f'Total emails found: {len(all_emails)}')
    print(f'Emails: {all_emails}')
    
    await ws.close()

asyncio.run(main())