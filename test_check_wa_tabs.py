import sys, json, time, asyncio, websockets, urllib.request
sys.path.insert(0, '/home/ubuntu')

async def check_wa_tabs():
    tabs_list = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/list"))
    wa_tabs = []
    for t in tabs_list:
        url = t.get('url', '')
        if 'web.whatsapp.com' in url and t.get('type') == 'page':
            wa_tabs.append(t)
    
    for tab in wa_tabs:
        print(f"\nTab: {tab.get('title')} - {tab.get('url')}")
        async with websockets.connect(tab['webSocketDebuggerUrl']) as ws:
            await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
            await ws.recv()
            
            expr = """(() => ({url: window.location.href, title: document.title, hasMain: !!document.querySelector('#main'), hasComposer: !!document.querySelector('[data-testid=\"conversation-compose-box-input\"]'), body: document.body.innerText.slice(0,300)}))()"""
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
                        print(f"  State: {msg2}")
                    break

asyncio.run(check_wa_tabs())