import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

async def process_profile():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    # Navigate to profile
    print('1. Navigating to /gigears/...')
    await ws.send(json.dumps({'id': 2, 'method': 'Page.navigate', 'params': {'url': 'https://www.instagram.com/gigears/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            print('Navigate result:', data)
            break
    
    await asyncio.sleep(5)
    
    # Check for email in bio
    print('2. Checking bio for email...')
    expr = r'(function() { const bio = document.querySelector("section main div[role=\"region\"]") || document.querySelector("section main div") || document.body; const text = bio.innerText || ""; const emails = text.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g); return JSON.stringify(emails || []); })()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            print('Emails in bio:', data)
            break
    
    # Check for "Contact" or email button
    print('3. Checking for contact button...')
    expr2 = r'(function() { const buttons = document.querySelectorAll("button, a[role=\"button\"]"); const contacts = []; buttons.forEach(b => { const text = (b.innerText || b.textContent || "").toLowerCase(); if (text.includes("contact") || text.includes("email") || text.includes("message")) { contacts.push({text: b.innerText, class: b.className}); } }); return JSON.stringify(contacts); })()'
    await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': expr2, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 4:
            print('Contact buttons:', data)
            break
    
    # Follow button
    print('4. Finding follow button...')
    expr3 = r'(function() { const btn = document.querySelector("button[type=\"button\"]") || document.querySelector("button"); if (btn) { const text = (btn.innerText || "").toLowerCase(); return JSON.stringify({text: btn.innerText, class: btn.className, disabled: btn.disabled}); } return null; })()'
    await ws.send(json.dumps({'id': 5, 'method': 'Runtime.evaluate', 'params': {'expression': expr3, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 5:
            print('Follow button:', data)
            break
    
    # Message button
    print('5. Finding message button...')
    expr4 = r'(function() { const btns = document.querySelectorAll("button, div[role=\"button\"]"); const msgBtns = []; btns.forEach(b => { const text = (b.innerText || "").toLowerCase(); if (text.includes("message") || text.includes("dm") || text.includes("send")) { msgBtns.push({text: b.innerText, class: b.className}); } }); return JSON.stringify(msgBtns); })()'
    await ws.send(json.dumps({'id': 6, 'method': 'Runtime.evaluate', 'params': {'expression': expr4, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 6:
            print('Message buttons:', data)
            break
    
    await ws.close()

asyncio.run(process_profile())