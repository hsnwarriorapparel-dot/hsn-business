import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

# Pick 3 that followed back
TARGETS = [
    {'handle': 'gorilla_bjj_academy', 'email': 'gorillabjjacademy@gmail.com', 'phone': '+1 201-962-8400'},
    {'handle': 'checkmatbristol', 'email': 'checkmatbristol@hotmail.com', 'phone': ''},
    {'handle': 'backbone_bjj', 'email': 'Backbonebjj@outlook.com', 'phone': '+1 951-776-6672'},
]

DM_MESSAGE = """Hi there! I'm reaching out from HSN Warrior Apparels, a martial arts sportswear manufacturer from Sialkot, Pakistan. We produce BJJ gis, rashguards, fight shorts, and team uniforms for academies worldwide.

If you're ever looking for custom apparel for your team or pro shop, I'd love to chat. Feel free to check our catalog at hsnwarriorapparels.vercel.app

Best regards,
HSN Warrior Apparels"""

async def send_dm(ws, target):
    handle = target['handle']
    print(f'\n=== SENDING DM to @{handle} ===')
    
    # Navigate to profile
    await ws.send(json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': f'https://www.instagram.com/{handle}/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 1:
            break
    
    await asyncio.sleep(4)
    
    # Click Message button
    expr_click_msg = r'(function() { const btns = document.querySelectorAll("button, div[role=\"button\"]"); for (const btn of btns) { if ((btn.innerText || "").trim().toLowerCase() === "message") { btn.click(); return {clicked: true}; } } return {clicked: false}; })()'
    await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': expr_click_msg, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            print(f'  Message click: {data["result"]["result"]["value"]}')
            break
    
    await asyncio.sleep(3)
    
    # Type message in composer
    expr_type = r'(function() { const inputs = document.querySelectorAll("div[role=\"textbox\"][contenteditable=\"true\"]"); for (const input of inputs) { if (input.offsetWidth > 0 && input.offsetHeight > 0) { input.focus(); input.innerText = arguments[0]; input.dispatchEvent(new Event("input", {bubbles: true})); return {typed: true}; } } return {typed: false}; })()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr_type, 'arguments': [DM_MESSAGE], 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            print(f'  Type result: {data["result"]["result"]["value"]}')
            break
    
    await asyncio.sleep(1)
    
    # Find and click Send button
    expr_send = r'(function() { const all = document.querySelectorAll("*"); for (const el of all) { const aria = el.getAttribute("aria-label") || ""; const text = (el.innerText || "").trim(); if ((aria.toLowerCase() === "send" || aria.toLowerCase() === "enviar" || text === "Send" || text === "Enviar") && el.offsetWidth > 0 && el.offsetHeight > 0) { el.click(); return {clicked: true, tag: el.tagName, aria, text, class: el.className}; } } return {clicked: false}; })()'
    await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': expr_send, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 4:
            print(f'  Send click: {data["result"]["result"]["value"]}')
            break
    
    await asyncio.sleep(2)
    
    # Verify in DM thread
    await ws.send(json.dumps({'id': 5, 'method': 'Page.navigate', 'params': {'url': 'https://www.instagram.com/direct/inbox/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 5:
            break
    
    await asyncio.sleep(4)
    
    expr_verify = r'(function() { const text = document.body.innerText; return text.includes("HSN Warrior Apparels") || text.includes("martial arts sportswear"); })()'
    await ws.send(json.dumps({'id': 6, 'method': 'Runtime.evaluate', 'params': {'expression': expr_verify, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 6:
            verified = data['result']['result']['value']
            print(f'  DM verified in inbox: {verified}')
            return verified
    
    return False

async def main():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 0, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    sent = 0
    for target in TARGETS:
        if await send_dm(ws, target):
            sent += 1
            print(f'  ✅ DM SENT AND VERIFIED to @{target["handle"]}')
        else:
            print(f'  ❌ DM NOT VERIFIED to @{target["handle"]}')
        await asyncio.sleep(3)
    
    print(f'\n=== TOTAL DMs VERIFIED SENT: {sent}/3 ===')
    
    await ws.close()

asyncio.run(main())