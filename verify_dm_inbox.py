import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

async def check_dm_inbox(ws):
    print('=== CHECKING INSTAGRAM DM INBOX ===')
    
    # Navigate to DM inbox
    await ws.send(json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': 'https://www.instagram.com/direct/inbox/'}}))
    for _ in range(20):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 1:
            break
    
    await asyncio.sleep(5)
    
    # Get all thread previews
    expr = r'(function() { const threads = document.querySelectorAll("div[role=\\"listitem\\"], div[role=\\"button\\"], a[href*=\"/direct/t/\"]"); const results = []; threads.forEach(t => { const text = t.innerText || ""; if (text.trim()) results.push(text.substring(0, 300)); }); return JSON.stringify(results); })()'
    await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            threads = json.loads(data['result'].get('value', '[]'))
            print(f'DM Threads found: {len(threads)}')
            for i, t in enumerate(threads[:20]):
                print(f'  {i+1}. {t}')
            break
    
    # Check for our message in specific threads
    targets = ['gorilla_bjj_academy', 'checkmatbristol', 'backbone_bjj', 'groundstonebjj', 'baysidebjj', 'cquencebjj', 'bellaartjiu', 'wiltshirebjjacademymarlborough']
    for target in targets:
        expr_search = f'(function() {{ const threads = document.querySelectorAll("div[role=\\"listitem\\"], div[role=\\"button\\"], a[href*=\"/direct/t/\"]"); const results = []; threads.forEach(t => {{ const text = t.innerText || ""; if (text.toLowerCase().includes("{target}")) results.push(text.substring(0, 500)); }}); return JSON.stringify(results); }})()'
        await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr_search, 'returnByValue': True}}))
        for _ in range(10):
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 3:
                results = json.loads(data['result'].get('value', '[]'))
                if results:
                    print(f'  FOUND thread for @{target}: {results}')
                else:
                    print(f'  NO thread for @{target}')
                break

async def main():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 0, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    await check_dm_inbox(ws)
    
    await ws.close()

asyncio.run(main())