import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

# Known major BJJ academies/gyms - likely to have business accounts with emails
KNOWN_ACADEMIES = [
    'graciebarra',
    'alliancebjj',
    'atosjiujitsu',
    'checkmat',
    'rogergracieacademy',
    'renzogracie',
    'marcelogarcia',
    'mendesbros',
    'art_of_jiu_jitsu',
    '10thplanetjiujitsu',
    'graciehumaita',
    'carlsongracie',
    'ribeirojiujitsu',
    'novabjiujitsu',
    'unityjiujitsu',
]

async def check_academy(ws, profile):
    print(f'\n=== @{profile} ===')
    
    # Navigate to profile
    await ws.send(json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': f'https://www.instagram.com/{profile}/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 1:
            break
    
    await asyncio.sleep(4)
    
    # Check for email and contact button
    expr = r'(function() { const allText = document.body.innerText; const emails = allText.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g); const contactBtns = []; document.querySelectorAll("button, div[role=\"button\"]").forEach(b => { const text = (b.innerText || "").toLowerCase(); if (text.includes("contact") || text.includes("email") || text.includes("call") || text.includes("phone")) contactBtns.push({text: b.innerText, class: b.className}); }); return JSON.stringify({emails: emails || [], contactBtns: contactBtns}); })()'
    await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            result = json.loads(data['result'].get('value', '{}'))
            print(f'   Emails: {result.get("emails", [])}')
            print(f'   Contact buttons: {result.get("contactBtns", [])}')
            return result.get('emails', [])
    
    return []

async def main():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 0, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    all_emails = []
    for profile in KNOWN_ACADEMIES:
        emails = await check_academy(ws, profile)
        all_emails.extend(emails)
        await asyncio.sleep(2)
    
    print('\n=== SUMMARY ===')
    print(f'Total emails found: {len(all_emails)}')
    print(f'Emails: {all_emails}')
    
    await ws.close()

asyncio.run(main())