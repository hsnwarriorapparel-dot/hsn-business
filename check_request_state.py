import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

async def check_request_state(ws):
    print('=== CHECKING MESSAGE REQUEST STATE ===')
    
    # Navigate and open DM
    await ws.send(json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': 'https://www.instagram.com/checkmatbristol/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 1:
            break
    
    await asyncio.sleep(4)
    
    # Click Message
    expr_msg = r'(function() { const btns = document.querySelectorAll("button, div[role=\"button\"]"); for (const btn of btns) { const text = (btn.innerText || "").toLowerCase(); if (text === "message") { btn.click(); return {clicked: true}; } } return {clicked: false}; })()'
    await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': expr_msg, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            break
    
    await asyncio.sleep(4)
    
    # Get full composer area text
    expr_full = r'(function() { const allText = document.body.innerText; return allText; })()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr_full, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            text = data['result'].get('value', '')
            # Find relevant lines
            lines = text.split('\n')
            relevant = [l.strip() for l in lines if any(kw in l.lower() for kw in ['request', 'pending', 'accept', 'follow', 'mutual', 'send', 'enviar', 'message', 'dm', 'direct', 'privacy', 'setting'])]
            print(f'  Relevant text ({len(relevant)} lines):')
            for l in relevant[:30]:
                print(f'    {l[:200]}')
            break

async def main():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 0, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    await check_request_state(ws)
    
    await ws.close()

asyncio.run(main())