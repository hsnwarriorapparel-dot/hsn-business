import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

TARGETS = [
    'gorilla_bjj_academy',
    'checkmatbristol',
    'backbone_bjj',
    'groundstonebjj',
    'baysidebjj',
]

async def check_profile(ws, handle):
    print(f'\n=== @{handle} ===')
    
    # Navigate to profile
    await ws.send(json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': f'https://www.instagram.com/{handle}/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 1:
            break
    
    await asyncio.sleep(4)
    
    # Check follow status
    expr_follow = r'(function() { const btns = document.querySelectorAll("button"); for (const btn of btns) { const text = (btn.innerText || "").toLowerCase(); if (text === "follow" || text === "following" || text === "requested" || text === "seguir" || text === "siguiendo") { return {text: btn.innerText, following: text === "following" || text === "siguiendo"}; } } return {text: "not found"}; })()'
    await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': expr_follow, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            print(f'  Follow status: {data["result"]["result"]["value"]}')
            break
    
    # Open DM composer
    expr_msg = r'(function() { const btns = document.querySelectorAll("button, div[role=\"button\"]"); for (const btn of btns) { const text = (btn.innerText || "").toLowerCase(); if (text === "message") { btn.click(); return {clicked: true}; } } return {clicked: false}; })()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr_msg, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            print(f'  Message button: {data["result"]["result"]["value"]}')
            break
    
    await asyncio.sleep(3)
    
    # Find ALL buttons in composer
    expr_btns = r'(function() { const btns = document.querySelectorAll("button, div[role=\"button\"]"); const results = []; btns.forEach(b => { const text = (b.innerText || "").trim(); if (text) results.push({text, class: b.className, tag: b.tagName, type: b.type}); }); return JSON.stringify(results); })()'
    await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': expr_btns, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 4:
            btns = json.loads(data['result'].get('value', '[]'))
            print(f'  Buttons in composer:')
            for b in btns:
                if any(kw in b['text'].lower() for kw in ['send', 'enviar', 'paper', 'plane', 'arrow']):
                    print(f'    SEND CANDIDATE: {b}')
            break

async def main():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 0, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    for handle in TARGETS:
        await check_profile(ws, handle)
        await asyncio.sleep(2)
    
    await ws.close()

asyncio.run(main())