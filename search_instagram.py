import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

async def search_instagram():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    # Try various search URLs
    search_urls = [
        'https://www.instagram.com/search?q=bjj%20gym',
        'https://www.instagram.com/search?q=jiu%20jitsu%20academy',
        'https://www.instagram.com/explore/search/?q=bjj%20gym',
        'https://www.instagram.com/web/search/topsearch/?context=blended&query=bjj%20gym',
        'https://www.instagram.com/web/search/topsearch/?query=bjj%20gym&context=blended',
    ]
    
    for url in search_urls:
        print(f'\n=== {url} ===')
        await ws.send(json.dumps({'id': 2, 'method': 'Page.navigate', 'params': {'url': url}}))
        for _ in range(15):
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 2:
                break
        
        await asyncio.sleep(5)
        
        # Get all text
        expr = r'(function() { return document.body.innerText.substring(0, 3000); })()'
        await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
        for _ in range(10):
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 3:
                text = data['result'].get('value', '')
                print(f'Response: {text[:500]}')
                break
    
    await ws.close()

asyncio.run(search_instagram())