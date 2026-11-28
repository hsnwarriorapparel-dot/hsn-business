import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

async def click_posts_get_profiles():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    # Navigate to hashtag
    print('1. Navigating to #bjjgym...')
    await ws.send(json.dumps({'id': 2, 'method': 'Page.navigate', 'params': {'url': 'https://www.instagram.com/explore/tags/bjjgym/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            break
    
    await asyncio.sleep(8)
    
    # Get post links
    print('2. Getting post links...')
    expr = r'(function() { const links = document.querySelectorAll("a[href^=\"/p/\"]"); const urls = []; links.forEach(l => urls.push(l.href)); return JSON.stringify(urls.slice(0, 10)); })()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            print('Post URLs:', data)
            break
    
    # Click each post and get profile
    profiles = []
    for i in range(5):
        print(f'\n--- Post {i+1} ---')
        # Click post
        expr2 = f'(function() {{ const links = document.querySelectorAll("a[href^=\"/p/\"]"); if (links[{i}]) {{ links[{i}].click(); return links[{i}].href; }} return null; }})()'
        await ws.send(json.dumps({'id': 10+i, 'method': 'Runtime.evaluate', 'params': {'expression': expr2, 'returnByValue': True}}))
        for _ in range(5):
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 10+i:
                print(f'Clicked: {data}')
                break
        
        await asyncio.sleep(4)
        
        # Get profile from post modal header
        expr3 = r'(function() { const header = document.querySelector("div[role=\"dialog\"] header") || document.querySelector("header"); if (header) { const links = header.querySelectorAll("a[href^=\"/\"]"); const profileLinks = []; links.forEach(a => { const href = a.getAttribute("href"); if (href && href.match(/^\/[^\/]+\/?$/)) profileLinks.push(href); }); return JSON.stringify(profileLinks); } return JSON.stringify([]); })()'
        await ws.send(json.dumps({'id': 20+i, 'method': 'Runtime.evaluate', 'params': {'expression': expr3, 'returnByValue': True}}))
        for _ in range(5):
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 20+i:
                print(f'Profiles: {data}')
                if data['result']['value']:
                    profiles.extend(json.loads(data['result']['value']))
                break
        
        # Close modal (press Escape)
        expr4 = r'(function() { document.body.dispatchEvent(new KeyboardEvent("keydown", {key: "Escape", bubbles: true})); return true; })()'
        await ws.send(json.dumps({'id': 30+i, 'method': 'Runtime.evaluate', 'params': {'expression': expr4, 'returnByValue': True}}))
        await asyncio.sleep(1)
    
    print('\n=== ALL PROFILES FOUND ===')
    print(profiles)
    await ws.close()

asyncio.run(click_posts_get_profiles())