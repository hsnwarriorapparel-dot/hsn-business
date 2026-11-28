import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

async def get_more_profiles():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    # Navigate to hashtag explore page
    print('1. Navigating to #bjjclub explore...')
    await ws.send(json.dumps({'id': 2, 'method': 'Page.navigate', 'params': {'url': 'https://www.instagram.com/explore/tags/bjjclub/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            break
    
    await asyncio.sleep(8)
    
    # Click multiple posts to get profiles
    print('2. Clicking posts to get profiles...')
    profiles = []
    for i in range(5):
        print(f'  Post {i+1}...')
        # Get post links
        expr = r'(function() { const links = document.querySelectorAll("a[href^=\"/p/\"]"); const urls = []; links.forEach(l => urls.push(l.href)); return JSON.stringify(urls.slice(0, 10)); })()'
        await ws.send(json.dumps({'id': 3+i, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
        for _ in range(5):
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 3+i:
                print(f'    Post URLs: {data}')
                break
        
        # Click first unvisited post
        expr2 = f'(function() {{ const links = document.querySelectorAll("a[href^=\"/p/\"]"); if (links[{i}]) {{ links[{i}].click(); return links[{i}].href; }} return null; }})()'
        await ws.send(json.dumps({'id': 10+i, 'method': 'Runtime.evaluate', 'params': {'expression': expr2, 'returnByValue': True}}))
        for _ in range(5):
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 10+i:
                print(f'    Clicked: {data}')
                break
        
        await asyncio.sleep(3)
        
        # Get profile from post header
        expr3 = r'(function() { const header = document.querySelector("header"); if (header) { const links = header.querySelectorAll("a[href^=\"/\"]"); const profileLinks = []; links.forEach(a => { const href = a.getAttribute("href"); if (href && href.match(/^\/[^\/]+\/?$/)) profileLinks.push(href); }); return JSON.stringify(profileLinks); } return JSON.stringify([]); })()'
        await ws.send(json.dumps({'id': 20+i, 'method': 'Runtime.evaluate', 'params': {'expression': expr3, 'returnByValue': True}}))
        for _ in range(5):
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 20+i:
                print(f'    Profiles: {data}')
                profiles.extend(json.loads(data['result']['value']))
                break
        
        await asyncio.sleep(2)
    
    print('All profiles found:', profiles)
    await ws.close()

asyncio.run(get_more_profiles())