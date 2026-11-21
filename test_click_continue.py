import sys, json, time, asyncio, websockets, urllib.request
sys.path.insert(0, '/home/ubuntu')

async def click_continue_on_share():
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
        
        # Find and click "Continue to WhatsApp Web" button
        expr = """
        (() => {
            const buttons = [...document.querySelectorAll('button, [role="button"], a')];
            for (const btn of buttons) {
                const text = (btn.innerText || btn.textContent || '').trim();
                if (text.includes('Continue to WhatsApp Web') || text.includes('Continue to Chat') || text.includes('Open WhatsApp Web')) {
                    console.log('Found button:', text, btn.tagName, btn.href);
                    btn.click();
                    return {found: true, text, tag: btn.tagName, href: btn.href};
                }
            }
            return {found: false};
        })()
        """
        await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": expr, "awaitPromise": True}}))
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get('id') == 2:
                print(f"Click result raw: {json.dumps(data, indent=2)}")
                result = data.get('result', {}).get('result', {})
                obj_id = result.get('objectId')
                if obj_id:
                    await ws.send(json.dumps({"id": 3, "method": "Runtime.getProperties", "params": {"objectId": obj_id, "ownProperties": True}}))
                    msg2 = await ws.recv()
                    print(f"Click properties: {msg2}")
                break
            elif 'method' in data:
                print(f"Event: {data['method']}")
        
        # Wait for navigation
        await asyncio.sleep(5)
        
        # Check if we're now on web.whatsapp.com
        expr2 = """(() => ({url: window.location.href, title: document.title}))()"""
        await ws.send(json.dumps({"id": 4, "method": "Runtime.evaluate", "params": {"expression": expr2, "awaitPromise": True}}))
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get('id') == 4:
                print(f"Check result raw: {json.dumps(data, indent=2)}")
                result = data.get('result', {}).get('result', {})
                obj_id = result.get('objectId')
                if obj_id:
                    await ws.send(json.dumps({"id": 5, "method": "Runtime.getProperties", "params": {"objectId": obj_id, "ownProperties": True}}))
                    msg2 = await ws.recv()
                    print(f"Check properties: {msg2}")
                break

asyncio.run(click_continue_on_share())