import sys, json, time, asyncio, websockets, urllib.request
sys.path.insert(0, '/home/ubuntu')

async def navigate_directly():
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
        
        # Directly navigate to the web.whatsapp.com URL
        expr = """(() => { window.location.href = 'https://web.whatsapp.com/send/?phone=34661571463&text&type=phone_number&app_absent=0'; return true; })()"""
        await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": expr, "awaitPromise": True}}))
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get('id') == 2:
                print(f"Navigate result: {json.dumps(data, indent=2)}")
                break
        
        # Wait for navigation and page load
        await asyncio.sleep(8)
        
        # Check if we're now on web.whatsapp.com
        expr2 = """(() => ({url: window.location.href, title: document.title, hasMain: !!document.querySelector('#main'), hasComposer: !!document.querySelector('[data-testid=\"conversation-compose-box-input\"]')}))()"""
        await ws.send(json.dumps({"id": 3, "method": "Runtime.evaluate", "params": {"expression": expr2, "awaitPromise": True}}))
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get('id') == 3:
                print(f"Check result raw: {json.dumps(data, indent=2)}")
                result = data.get('result', {}).get('result', {})
                obj_id = result.get('objectId')
                if obj_id:
                    await ws.send(json.dumps({"id": 4, "method": "Runtime.getProperties", "params": {"objectId": obj_id, "ownProperties": True}}))
                    msg2 = await ws.recv()
                    print(f"Check properties: {msg2}")
                break

asyncio.run(navigate_directly())