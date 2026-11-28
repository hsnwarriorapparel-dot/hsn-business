import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

async def check_followers():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    # Navigate to a known gym's followers
    print('1. Navigating to graciebarra followers...')
    await ws.send(json.dumps({'id': 2, 'method': 'Page.navigate', 'params': {'url': 'https://www.instagram.com/graciebarra/followers/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            break
    
    await asyncio.sleep(5)
    
    # Get all links
    print('2. Getting follower links...')
    expr = r'(function() { const links = []; document.querySelectorAll("a[href^=\"/\"]").forEach(a => { const href = a.getAttribute("href"); if (href && href.match(/^\/[^\/]+\/?$/)) links.push(href); }); return JSON.stringify([...new Set(links)].slice(0, 50)); })()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            print('Follower links:', data)
            break
    
    # Scroll
    print('3. Scrolling...')
    for i in range(5):
        await ws.send(json.dumps({'id': 10+i, 'method': 'Runtime.evaluate', 'params': {'expression': 'document.querySelector("div[role=\"dialog\"]")?.scrollTo(0, document.querySelector("div[role=\"dialog\"]").scrollHeight) || window.scrollTo(0, document.body.scrollHeight);', 'returnByValue': True}}))
        await asyncio.sleep(2)
    
    print('4. Getting links after scroll...')
    await ws.send(json.dumps({'id': 20, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 20:
            print('Links after scroll:', data)
            break
    
    await ws.close()

asyncio.run(check_followers())