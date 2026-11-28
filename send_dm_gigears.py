import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

async def send_dm():
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
            print('Message click:', data)
            break
    
    await asyncio.sleep(3)
    
    # Type DM using correct selector
    print('3. Typing DM...')
    dm_text = "Hi! We're HSN Warrior Apparels from Sialkot, Pakistan - manufacturer of BJJ/Judo/Karate/MMA gear. Interested in wholesale/OEM? DM for catalog."
    expr3 = f'(function() {{ const textarea = document.querySelector("div[role=\\"textbox\\"][contenteditable=\\"true\\"].xzsf02u"); if (textarea) {{ textarea.focus(); textarea.innerText = `{dm_text.replace("`", "\\\\`").replace("${", "\\\\${")}`; textarea.dispatchEvent(new Event("input", {{bubbles: true}})); return true; }} return false; }})()'
    await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': expr3, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 4:
            print('Type DM:', data)
            break
    
    await asyncio.sleep(1)
    
    # Send DM
    print('4. Sending DM...')
    expr4 = r'(function() { const btns = document.querySelectorAll("button, div[role=\"button\"]"); for (const btn of btns) { const text = (btn.innerText || "").toLowerCase(); if (text === "send") { btn.click(); return {clicked: true, text: btn.innerText}; } } return {clicked: false}; })()'
    await ws.send(json.dumps({'id': 5, 'method': 'Runtime.evaluate', 'params': {'expression': expr4, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 5:
            print('Send click:', data)
            break
    
    await asyncio.sleep(2)
    
    # Verify DM sent (check if thread has message)
    print('5. Verifying DM sent...')
    expr5 = r'(function() { const msgs = document.querySelectorAll("div[role=\"log\"] div, article div"); const texts = []; msgs.forEach(m => { const t = m.innerText; if (t && t.includes("HSN Warrior")) texts.push(t.substring(0, 100)); }); return JSON.stringify(texts); })()'
    await ws.send(json.dumps({'id': 6, 'method': 'Runtime.evaluate', 'params': {'expression': expr5, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 6:
            print('DM verification:', data)
            break
    
    await ws.close()

asyncio.run(send_dm())