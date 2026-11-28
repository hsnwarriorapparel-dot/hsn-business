import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

async def check_followers(ws):
    print('=== CHECKING FOLLOWERS / FOLLOWING ===')
    
    # Go to profile
    await ws.send(json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': 'https://www.instagram.com/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 1:
            break
    
    await asyncio.sleep(4)
    
    # Get username
    expr_user = r'(function() { const el = document.querySelector("header a[href^=\"/\"] span"); return el ? el.innerText : ""; })()'
    await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': expr_user, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            username = data['result'].get('value', '')
            print(f'  Current user: @{username}')
            break
    
    # Check followers
    await ws.send(json.dumps({'id': 3, 'method': 'Page.navigate', 'params': {'url': f'https://www.instagram.com/{username}/followers/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            break
    
    await asyncio.sleep(5)
    
    expr_followers = r'(function() { const items = document.querySelectorAll("div[role=\"listitem\"] a, a[href^=\"/\"]"); const results = []; items.forEach(a => { const href = a.href; const text = a.innerText; if (href && href.includes("instagram.com/") && !href.includes("/followers") && !href.includes("/following")) { results.push({href, text}); } }); return JSON.stringify(results); })()'
    await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': expr_followers, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 4:
            results = json.loads(data['result'].get('value', '[]'))
            print(f'  Followers found: {len(results)}')
            for r in results[:20]:
                print(f'    {r}')
            break

async def main():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 0, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    await check_followers(ws)
    
    await ws.close()

asyncio.run(main())