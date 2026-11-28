import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

async def explore_instagram():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    # Navigate to hashtag explore page for BJJ
    print('1. Navigating to #bjjclub explore...')
    await ws.send(json.dumps({'id': 2, 'method': 'Page.navigate', 'params': {'url': 'https://www.instagram.com/explore/tags/bjjclub/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            print('Navigate result:', data)
            break
    
    await asyncio.sleep(5)
    
    # Get profile links from posts
    print('2. Extracting profile links from posts...')
    expr = r'(function() { const links = []; document.querySelectorAll("a[href^=\"/\"]").forEach(a => { const href = a.getAttribute("href"); if (href && href.match(/^\/[^\/]+\/?$/)) { links.push(href); } }); return JSON.stringify([...new Set(links)].slice(0, 20)); })()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
    for _ in range(5):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            print('Profile links:', data)
            break
    
    await ws.close()

asyncio.run(explore_instagram())