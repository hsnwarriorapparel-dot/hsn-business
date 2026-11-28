import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

GYMS = [
    {'handle': 'gorilla_bjj_academy', 'email': 'gorillabjjacademy@gmail.com'},
    {'handle': 'checkmatbristol', 'email': 'checkmatbristol@hotmail.com'},
    {'handle': 'backbone_bjj', 'email': 'Backbonebjj@outlook.com'},
    {'handle': 'groundstonebjj', 'email': 'groundstonebjj@yahoo.com'},
    {'handle': 'baysidebjj', 'email': 'baysidebjj@outlook.com'},
]

async def check_contact(ws, gym, gym_num):
    handle = gym['handle']
    print(f'\n=== GYM {gym_num}: @{handle} ===')
    
    await ws.send(json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': f'https://www.instagram.com/{handle}/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 1:
            break
    
    await asyncio.sleep(5)
    
    # Check for Contact button and click it
    expr_contact = r'(function() { const btns = document.querySelectorAll("button, div[role=\"button\"]"); const results = []; btns.forEach(b => { const text = (b.innerText || "").toLowerCase(); if (text.includes("contact") || text.includes("email") || text.includes("call") || text.includes("phone")) { results.push({text: b.innerText, class: b.className}); b.click(); } }); return JSON.stringify(results); })()'
    await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': expr_contact, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            contact = json.loads(data['result'].get('value', '[]'))
            print(f'   Contact buttons clicked: {contact}')
            break
    
    await asyncio.sleep(3)
    
    # Check for email in any modal that opened
    expr_email = r'(function() { const allText = document.body.innerText; const emails = allText.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g); return JSON.stringify(emails || []); })()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr_email, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            emails = json.loads(data['result'].get('value', '[]'))
            print(f'   Emails after contact click: {emails}')
            break

async def main():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 0, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    for i, gym in enumerate(GYMS, 1):
        await check_contact(ws, gym, i)
        await asyncio.sleep(3)
    
    await ws.close()

asyncio.run(main())