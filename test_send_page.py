import sys, json, time, asyncio, websockets, urllib.request
sys.path.insert(0, '/home/ubuntu')

async def wait_and_click_send_page():
    tabs_list = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/list"))
    send_tab = None
    for t in tabs_list:
        url = t.get('url', '')
        if 'web.whatsapp.com/send' in url and t.get('type') == 'page':
            send_tab = t
            break
    
    if not send_tab:
        print("Send page tab not found")
        return False
    
    print(f"Send tab: {send_tab.get('url')}")
    
    async with websockets.connect(send_tab['webSocketDebuggerUrl']) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
        await ws.recv()
        
        # Wait longer for page to fully load
        await asyncio.sleep(10)
        
        # Check page state
        expr = """(() => ({url: window.location.href, title: document.title, hasMain: !!document.querySelector('#main'), hasComposer: !!document.querySelector('[data-testid=\"conversation-compose-box-input\"]'), body: document.body.innerText.slice(0,500)}))()"""
        await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": expr, "awaitPromise": True}}))
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get('id') == 2:
                result = data.get('result', {}).get('result', {})
                obj_id = result.get('objectId')
                if obj_id:
                    await ws.send(json.dumps({"id": 3, "method": "Runtime.getProperties", "params": {"objectId": obj_id, "ownProperties": True}}))
                    msg2 = await ws.recv()
                    print(f"Check properties: {msg2}")
                break
        
        # Click "Continue to Chat" on the send page
        click_expr = """
        (() => {
            const buttons = [...document.querySelectorAll('button, [role="button"], a')];
            for (const btn of buttons) {
                const text = (btn.innerText || btn.textContent || '').trim();
                if (text.includes('Continue') || text.includes('Chat') || text.includes('Open')) {
                    console.log('Found:', text);
                    btn.click();
                    return {found: true, text: text};
                }
            }
            return {found: false};
        })()
        """
        await ws.send(json.dumps({"id": 4, "method": "Runtime.evaluate", "params": {"expression": click_expr, "awaitPromise": True}}))
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get('id') == 4:
                result = data.get('result', {}).get('result', {})
                obj_id = result.get('objectId')
                if obj_id:
                    await ws.send(json.dumps({"id": 5, "method": "Runtime.getProperties", "params": {"objectId": obj_id, "ownProperties": True}}))
                    msg2 = await ws.recv()
                    print(f"Click properties: {msg2}")
                break
        
        # Wait for chat to open
        await asyncio.sleep(5)
        
        # Check final state
        expr2 = """(() => ({url: window.location.href, title: document.title, hasMain: !!document.querySelector('#main'), hasComposer: !!document.querySelector('[data-testid=\"conversation-compose-box-input\"]')}))()"""
        await ws.send(json.dumps({"id": 6, "method": "Runtime.evaluate", "params": {"expression": expr2, "awaitPromise": True}}))
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get('id') == 6:
                result = data.get('result', {}).get('result', {})
                obj_id = result.get('objectId')
                if obj_id:
                    await ws.send(json.dumps({"id": 7, "method": "Runtime.getProperties", "params": {"objectId": obj_id, "ownProperties": True}}))
                    msg2 = await ws.recv()
                    print(f"Final check properties: {msg2}")
                break

asyncio.run(wait_and_click_send_page())