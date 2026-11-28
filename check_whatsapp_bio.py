import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

GYMS = [
    {'handle': 'gorilla_bjj_academy', 'email': 'gorillabjjacademy@gmail.com'},
    {'handle': 'checkmatbristol', 'email': 'checkmatbristol@hotmail.com'},
    {'handle': 'combatevolutionbjj', 'email': 'combatjiujitsu@yahoo.com'},
    {'handle': 'backbone_bjj', 'email': 'Backbonebjj@outlook.com'},
    {'handle': 'groundstonebjj', 'email': 'groundstonebjj@yahoo.com'},
    {'handle': 'baysidebjj', 'email': 'baysidebjj@outlook.com'},
    {'handle': 'cquencebjj', 'email': 'cquencebjj@yahoo.com'},
    {'handle': 'bellaartjiu', 'email': 'bellaart@outlook.com'},
    {'handle': 'wiltshirebjjacademymarlborough', 'email': 'wiltshirebjjacademy@gmail.com'},
]

async def check_profile(ws, gym):
    handle = gym['handle']
    print(f'\n=== @{handle} ===')
    
    await ws.send(json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': f'https://www.instagram.com/{handle}/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 1:
            break
    
    await asyncio.sleep(5)
    
    # Get full bio text
    expr_bio = r'(function() { const allText = document.body.innerText; return allText; })()'
    await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': expr_bio, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            text = data['result'].get('value', '')
            # Search for WhatsApp, phone, contact
            lines = text.split('\n')
            contact_lines = [l.strip() for l in lines if any(kw in l.lower() for kw in ['whatsapp', 'wa.me', 'phone', 'call', 'contact', '+', 'mobile', 'tel:', 'zap', 'zap:'])]
            print(f'  Contact lines: {contact_lines[:10]}')
            
            # Check for email in bio
            import re
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
            print(f'  Emails in bio: {emails}')
            break
    
    # Check external links (website button)
    expr_links = r'(function() { const links = document.querySelectorAll("a[href^=\"http\"]"); const results = []; links.forEach(l => { if (!l.href.includes("instagram.com") && !l.href.includes("facebook.com") && !l.href.includes("cdninstagram") && !l.href.includes("google.com")) results.push({href: l.href, text: l.innerText}); }); return JSON.stringify(results); })()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr_links, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            links = json.loads(data['result'].get('value', '[]'))
            print(f'  External links: {links}')
            break

async def main():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 0, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    for gym in GYMS:
        await check_profile(ws, gym)
        await asyncio.sleep(2)
    
    await ws.close()

asyncio.run(main())