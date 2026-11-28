import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

async def mobile_instagram():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    # Try mobile Instagram
    urls = [
        'https://m.instagram.com/explore/tags/bjjgym/',
        'https://m.instagram.com/graciebarra/',
        'https://m.instagram.com/search?q=bjj%20gym',
    ]
    
    for url in urls:
        print(f'\n=== {url} ===')
        await ws.send(json.dumps({'id': 2, 'method': 'Page.navigate', 'params': {'url': url}}))
        for _ in range(15):
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 2:
                break
        
        await asyncio.sleep(5)
        
        # Get all links
        expr = r'(function() { const links = []; document.querySelectorAll("a[href]").forEach(a => links.push(a.href)); return JSON.stringify([...new Set(links)].slice(0, 50)); })()'
        await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
        for _ in range(10):
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 3:
                print(f'Links: {data}')
                break
        
        # Get text
        expr2 = r'(function() { return document.body.innerText.substring(0, 2000); })()'
        await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': expr2, 'returnByValue': True}}))
        for _ in range(10):
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 4:
                text = data['result'].get('value', '')
                print(f'Text: {text[:500]}')
                break
    
    await ws.close()

asyncio.run(mobile_instagram())