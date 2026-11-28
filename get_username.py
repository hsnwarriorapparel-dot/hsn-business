import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

async def get_current_user(ws):
    # Navigate to a known profile to get username from header
    await ws.send(json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': 'https://www.instagram.com/gorilla_bjj_academy/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 1:
            break
    
    await asyncio.sleep(4)
    
    # Get all text to find username
    expr = r'(function() { return document.body.innerText; })()'
    await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            text = data['result'].get('value', '')
            # Look for @username patterns
            import re
            handles = re.findall(r'@[a-zA-Z0-9_.]+', text)
            print(f'  Found handles: {handles[:30]}')
            break

async def main():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 0, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    await get_current_user(ws)
    
    await ws.close()

asyncio.run(main())