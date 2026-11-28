import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

GYMS = [
    'gorilla_bjj_academy',
    'checkmatbristol',
    'combatevolutionbjj',
    'backbone_bjj',
    'groundstonebjj',
    'baysidebjj',
    'cquencebjj',
    'bellaartjiu',
    'wiltshirebjjacademymarlborough',
]

async def check_follow_back(ws, handle):
    print(f'\n=== @{handle} ===')
    
    await ws.send(json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': f'https://www.instagram.com/{handle}/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 1:
            break
    
    await asyncio.sleep(4)
    
    # Check follow button text
    expr_follow = r'(function() { const btns = document.querySelectorAll("button"); for (const btn of btns) { const text = (btn.innerText || "").trim(); if (text === "Follow" || text === "Following" || text === "Requested" || text === "Seguir" || text === "Siguiendo" || text === "Solicitado") { return {text}; } } return {text: "not found"}; })()'
    await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': expr_follow, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            follow_text = data['result']['result']['value']['text']
            print(f'  Follow button: {follow_text}')
            break
    
    # Check Message button
    expr_msg = r'(function() { const btns = document.querySelectorAll("button, div[role=\"button\"]"); for (const btn of btns) { const text = (btn.innerText || "").trim().toLowerCase(); if (text === "message") { return {found: true}; } } return {found: false}; })()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr_msg, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            msg = data['result']['result']['value']
            print(f'  Message button: {msg}')
            break
    
    if follow_text == "Following" and msg.get('found'):
        print(f'  >>> FOLLOWS BACK - Can DM!')
        return True
    
    return False

async def main():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 0, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    follow_backs = []
    for handle in GYMS:
        if await check_follow_back(ws, handle):
            follow_backs.append(handle)
        await asyncio.sleep(2)
    
    print(f'\n=== FOLLOWS BACK (can DM): {follow_backs} ===')
    
    await ws.close()

asyncio.run(main())