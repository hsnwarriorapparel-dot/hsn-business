import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

async def follow_and_dm():
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
            break
    
    await asyncio.sleep(5)
    
    # Click Follow button
    print('2. Clicking Follow button...')
    expr = r'(function() { const btns = document.querySelectorAll("button"); for (const btn of btns) { const text = (btn.innerText || "").toLowerCase(); if (text === "follow" || text === "seguir") { btn.click(); return {clicked: true, text: btn.innerText}; } } return {clicked: false}; })()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            print('Follow click:', data)
            break
    
    await asyncio.sleep(2)
    
    # Click Message button
    print('3. Clicking Message button...')
    expr2 = r'(function() { const btns = document.querySelectorAll("button, div[role=\"button\"]"); for (const btn of btns) { const text = (btn.innerText || "").toLowerCase(); if (text === "message") { btn.click(); return {clicked: true, text: btn.innerText}; } } return {clicked: false}; })()'
    await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': expr2, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 4:
            print('Message click:', data)
            break
    
    await asyncio.sleep(3)
    
    # Type DM
    print('4. Typing DM...')
    dm_text = "Hi! We're HSN Warrior Apparels from Sialkot, Pakistan - manufacturer of BJJ/Judo/Karate/MMA gear. Interested in wholesale/OEM? DM for catalog."
    expr3 = f'(function() {{ const textarea = document.querySelector("textarea[placeholder*=\\"Message\\" i]") || document.querySelector("div[role=\\"textbox\\"][contenteditable=\\"true\\"]"); if (textarea) {{ textarea.focus(); textarea.value = `{dm_text.replace("`", "\\\\`").replace("${", "\\\\${")}`; textarea.dispatchEvent(new Event("input", {{bubbles: true}})); return true; }} return false; }})()'
    await ws.send(json.dumps({'id': 5, 'method': 'Runtime.evaluate', 'params': {'expression': expr3, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 5:
            print('Type DM:', data)
            break
    
    await asyncio.sleep(1)
    
    # Send DM
    print('5. Sending DM...')
    expr4 = r'(function() { const btns = document.querySelectorAll("button, div[role=\"button\"]"); for (const btn of btns) { const text = (btn.innerText || "").toLowerCase(); if (text === "send") { btn.click(); return {clicked: true, text: btn.innerText}; } } return {clicked: false}; })()'
    await ws.send(json.dumps({'id': 6, 'method': 'Runtime.evaluate', 'params': {'expression': expr4, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 6:
            print('Send click:', data)
            break
    
    await asyncio.sleep(2)
    
    # Check for email in contact options
    print('6. Checking for email in contact...')
    expr5 = r'(function() { const allText = document.body.innerText; const emails = allText.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g); return JSON.stringify(emails || []); })()'
    await ws.send(json.dumps({'id': 7, 'method': 'Runtime.evaluate', 'params': {'expression': expr5, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 7:
            print('Emails found:', data)
            break
    
    await ws.close()

asyncio.run(follow_and_dm())