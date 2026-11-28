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
    
    # Navigate directly to first post URL
    print('3. Navigating directly to first post...')
    await ws.send(json.dumps({'id': 4, 'method': 'Page.navigate', 'params': {'url': 'https://www.instagram.com/p/DXwE0H6E39J/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 4:
            break
    
    await asyncio.sleep(5)
    
    # Get profile from post page header
    print('4. Getting profile from post page...')
    expr3 = r'(function() { const header = document.querySelector("header"); if (header) { const links = header.querySelectorAll("a[href^=\"/\"]"); const profileLinks = []; links.forEach(a => { const href = a.getAttribute("href"); if (href && href.match(/^\/[^\/]+\/?$/)) profileLinks.push(href); }); return JSON.stringify(profileLinks); } return JSON.stringify([]); })()'
    await ws.send(json.dumps({'id': 5, 'method': 'Runtime.evaluate', 'params': {'expression': expr3, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 5:
            print('Profiles:', data)
            break
    
    # Try more posts
    post_urls = [
        'https://www.instagram.com/p/DcHBCmBpO2Q/',
        'https://www.instagram.com/p/Df_NfaxPyaY/',
        'https://www.instagram.com/p/DfUtXT9OqDV/',
        'https://www.instagram.com/p/DgNap8fTgcZ/'
    ]
    
    profiles = []
    for url in post_urls:
        print(f'\n--- Post: {url} ---')
        await ws.send(json.dumps({'id': 10, 'method': 'Page.navigate', 'params': {'url': url}}))
        for _ in range(15):
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 10:
                break
        
        await asyncio.sleep(5)
        
        expr3 = r'(function() { const header = document.querySelector("header"); if (header) { const links = header.querySelectorAll("a[href^=\"/\"]"); const profileLinks = []; links.forEach(a => { const href = a.getAttribute("href"); if (href && href.match(/^\/[^\/]+\/?$/)) profileLinks.push(href); }); return JSON.stringify(profileLinks); } return JSON.stringify([]); })()'
        await ws.send(json.dumps({'id': 11, 'method': 'Runtime.evaluate', 'params': {'expression': expr3, 'returnByValue': True}}))
        for _ in range(10):
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 11:
                print('Profiles:', data)
                val = data['result'].get('value', '[]')
                profiles.extend(json.loads(val))
                break
    
    print('\n=== ALL PROFILES FOUND ===')
    print(list(set(profiles)))
    await ws.close()

asyncio.run(click_posts_get_profiles())