import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

async def verify_dm():
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
    
    # Click Message button
    print('2. Clicking Message button...')
    expr2 = r'(function() { const btns = document.querySelectorAll("button, div[role=\"button\"]"); for (const btn of btns) { const text = (btn.innerText || "").toLowerCase(); if (text === "message") { btn.click(); return {clicked: true, text: btn.innerText}; } } return {clicked: false}; })()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr2, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            break
    
    await asyncio.sleep(3)
    
    # Type DM
    print('3. Typing DM...')
    dm_text = "Hi! We're HSN Warrior Apparels from Sialkot, Pakistan - manufacturer of BJJ/Judo/Karate/MMA gear. Interested in wholesale/OEM? DM for catalog."
    expr3 = f'(function() {{ const textarea = document.querySelector("div[role=\\"textbox\\"][contenteditable=\\"true\\"].xzsf02u"); if (textarea) {{ textarea.focus(); textarea.innerText = `{dm_text.replace("`", "\\\\`").replace("${", "\\\\${")}`; textarea.dispatchEvent(new Event("input", {{bubbles: true}})); return true; }} return false; }})()'
    await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': expr3, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 4:
            break
    
    await asyncio.sleep(1)
    
    # Try Ctrl+Enter
    print('4. Trying Ctrl+Enter...')
    expr4 = r'(function() { const textarea = document.querySelector("div[role=\"textbox\"][contenteditable=\"true\"].xzsf02u"); if (textarea) { textarea.focus(); textarea.dispatchEvent(new KeyboardEvent("keydown", {key: "Enter", ctrlKey: true, bubbles: true})); return true; } return false; })()'
    await ws.send(json.dumps({'id': 5, 'method': 'Runtime.evaluate', 'params': {'expression': expr4, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 5:
            break
    
    await asyncio.sleep(3)
    
    # Check DM thread content
    print('5. Checking DM thread...')
    expr5 = r'(function() { const threads = document.querySelectorAll("div[role=\"log\"] > div, article"); const texts = []; threads.forEach(t => { const text = t.innerText; if (text && text.length > 10) texts.push(text.substring(0, 200)); }); return JSON.stringify(texts.slice(0, 10)); })()'
    await ws.send(json.dumps({'id': 6, 'method': 'Runtime.evaluate', 'params': {'expression': expr5, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 6:
            print('Thread content:', data)
            break
    
    # Navigate to inbox to verify
    print('6. Navigating to inbox...')
    await ws.send(json.dumps({'id': 7, 'method': 'Page.navigate', 'params': {'url': 'https://www.instagram.com/direct/inbox/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 7:
            break
    
    await asyncio.sleep(5)
    
    # Find gigears thread
    print('7. Finding gigears thread...')
    expr7 = r'(function() { const threads = document.querySelectorAll("div[role=\"listitem\"], div[role=\"button\"]"); const results = []; threads.forEach(t => { const text = t.innerText; if (text && text.toLowerCase().includes("gigears")) results.push(text.substring(0, 200)); }); return JSON.stringify(results); })()'
    await ws.send(json.dumps({'id': 8, 'method': 'Runtime.evaluate', 'params': {'expression': expr7, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 8:
            print('Inbox threads:', data)
            break
    
    await ws.close()

asyncio.run(verify_dm())