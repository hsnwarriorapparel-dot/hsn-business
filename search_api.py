import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

async def search_api():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    # Try Instagram's search endpoint
    print('1. Trying search API...')
    search_urls = [
        'https://www.instagram.com/web/search/topsearch/?query=bjj%20academy',
        'https://www.instagram.com/web/search/topsearch/?query=martial%20arts%20gym',
        'https://www.instagram.com/web/search/topsearch/?query=jiu%20jitsu%20club',
    ]
    
    for url in search_urls:
        print(f'\n--- {url} ---')
        await ws.send(json.dumps({'id': 2, 'method': 'Page.navigate', 'params': {'url': url}}))
        for _ in range(15):
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 2:
                break
        
        await asyncio.sleep(3)
        
        # Get page content
        expr = r'(function() { return document.body.innerText; })()'
        await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
        for _ in range(10):
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 3:
                text = data['result'].get('value', '')
                print(f'Response (first 2000 chars): {text[:2000]}')
                break
    
    await ws.close()

asyncio.run(search_api())