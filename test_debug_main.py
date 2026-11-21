import sys, json, time, asyncio, websockets
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs

async def debug_main_area():
    tabs = get_tabs()
    wa = [t for t in tabs if 'web.whatsapp.com' in (t.get('url') or '') and t.get('type') == 'page']
    if not wa:
        print('NO WA TAB')
        return
    ws_url = wa[0]['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
        await ws.recv()
        
        # Check main area
        check_main = """
        (() => {
            const main = document.querySelector('#main');
            if (!main) return {main: false};
            
            const contentEditables = [...main.querySelectorAll('[contenteditable="true"]')];
            const buttons = [...main.querySelectorAll('button, [role="button"], span[data-icon]')];
            
            return {
                main: true,
                contentEditables: contentEditables.map(e => ({
                    tag: e.tagName,
                    class: e.className.slice(0,100),
                    testid: e.getAttribute('data-testid'),
                    tab: e.getAttribute('data-tab'),
                    aria: e.getAttribute('aria-label'),
                    text: (e.innerText || e.textContent || '').slice(0,100)
                })),
                buttons: buttons.map(b => ({
                    tag: b.tagName,
                    class: b.className.slice(0,100),
                    aria: b.getAttribute('aria-label'),
                    testid: b.getAttribute('data-testid'),
                    icon: b.getAttribute('data-icon'),
                    disabled: b.disabled
                })).filter(b => b.aria || b.testid || b.icon)
            };
        })()
        """
        await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": check_main, "awaitPromise": True}}))
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get('id') == 2:
                result = data.get('result', {})
                obj_id = result.get('result', {}).get('objectId')
                if obj_id:
                    await ws.send(json.dumps({"id": 3, "method": "Runtime.getProperties", "params": {"objectId": obj_id, "ownProperties": True}}))
                    msg2 = await ws.recv()
                    data2 = json.loads(msg2)
                    # Print the properties
                    for prop in data2.get('result', {}).get('result', []):
                        if prop.get('value', {}).get('type') == 'object':
                            obj_id2 = prop['value']['objectId']
                            await ws.send(json.dumps({"id": 4, "method": "Runtime.getProperties", "params": {"objectId": obj_id2, "ownProperties": True}}))
                            msg3 = await ws.recv()
                            print(f"Property {prop['name']}: {msg3}")
                break
            elif 'method' in data:
                pass

asyncio.run(debug_main_area())