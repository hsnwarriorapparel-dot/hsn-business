import sys, json, time, asyncio, websockets, urllib.request
sys.path.insert(0, '/home/ubuntu')

async def debug_share_page():
    tabs_list = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/list"))
    share_tab = None
    for t in tabs_list:
        url = t.get('url', '')
        if 'api.whatsapp.com/send' in url and t.get('type') == 'page':
            share_tab = t
            break
    
    if not share_tab:
        print("Share page tab not found")
        return False
    
    print(f"Share tab: {share_tab.get('url')}")
    
    async with websockets.connect(share_tab['webSocketDebuggerUrl']) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
        await ws.recv()
        
        # Get page info
        expr = """(() => ({url: window.location.href, title: document.title, body: document.body.innerText.slice(0,500)}))()"""
        await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": expr, "awaitPromise": True}}))
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get('id') == 2:
                print(f"Page info raw: {json.dumps(data, indent=2)}")
                result = data.get('result', {}).get('result', {})
                obj_id = result.get('objectId')
                if obj_id:
                    await ws.send(json.dumps({"id": 3, "method": "Runtime.getProperties", "params": {"objectId": obj_id, "ownProperties": True}}))
                    msg2 = await ws.recv()
                    print(f"Properties: {msg2}")
                break
            elif 'method' in data:
                print(f"Event: {data['method']}")

asyncio.run(debug_share_page())