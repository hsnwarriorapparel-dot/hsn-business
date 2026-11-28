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
    
    await asyncio.sleep(8)
    
    # Click on first post
    print('2. Clicking first post...')
    expr = r'(function() { const link = document.querySelector("a[href^=\"/p/\"]"); if (link) { link.click(); return link.href; } return null; })()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            print('Click result:', data)
            break
    
    await asyncio.sleep(5)
    
    # Get profile link from post header
    print('3. Getting profile link from post header...')
    expr2 = r'(function() { const header = document.querySelector("header"); if (header) { const links = header.querySelectorAll("a[href^=\"/\"]"); const profileLinks = []; links.forEach(a => { const href = a.getAttribute("href"); if (href && href.match(/^\/[^\/]+\/?$/)) profileLinks.push(href); }); return JSON.stringify(profileLinks); } return JSON.stringify([]); })()'
    await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': expr2, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 4:
            print('Profile links from post header:', data)
            break
    
    await ws.close()

asyncio.run(explore_instagram())