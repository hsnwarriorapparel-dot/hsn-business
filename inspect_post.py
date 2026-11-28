import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

async def inspect_post():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    # Navigate to post
    print('1. Navigating to post...')
    await ws.send(json.dumps({'id': 2, 'method': 'Page.navigate', 'params': {'url': 'https://www.instagram.com/p/DXwE0H6E39J/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            break
    
    await asyncio.sleep(5)
    
    # Get all links on page
    print('2. All links on post page...')
    expr = r'(function() { const links = []; document.querySelectorAll("a[href]").forEach(a => { links.push(a.href); }); return JSON.stringify([...new Set(links)].slice(0, 50)); })()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            print('All links:', data)
            break
    
    # Get article content
    print('3. Article content...')
    expr2 = r'(function() { const article = document.querySelector("article"); if (article) return article.innerHTML.substring(0, 5000); return ""; })()'
    await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': expr2, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 4:
            print('Article HTML:', data)
            break
    
    await ws.close()

asyncio.run(inspect_post())