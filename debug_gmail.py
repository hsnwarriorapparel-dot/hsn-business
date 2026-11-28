import asyncio
import websockets
import json

ws_url = 'ws://localhost:9222/devtools/page/B93A66E395208FCD2D9B994E0CCABB9A'

async def debug_gmail_compose():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    # Try to find and click Compose button
    print('1. Finding Compose button...')
    expr = r'document.querySelector("div[role=\"button\"][aria-label*=\"Compose\"]")'
    await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': expr}}))
    for _ in range(5):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            print('Compose button result:', data)
            break
    
    # Click it
    print('2. Clicking Compose...')
    expr2 = r'(function() { var btn = document.querySelector("div[role=\"button\"][aria-label*=\"Compose\"]"); if(btn) { btn.click(); return true; } return false; })()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr2}}))
    for _ in range(5):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            print('Click result:', data)
            break
    
    await asyncio.sleep(3)
    
    # Check for To field
    print('3. Checking for To field...')
    expr3 = r'document.querySelector("div[role=\"listbox\"]")'
    await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': expr3}}))
    for _ in range(5):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 4:
            print('To field result:', data)
            break
    
    await ws.close()

asyncio.run(debug_gmail_compose())