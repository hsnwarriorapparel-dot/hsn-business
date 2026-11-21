import sys, json, time, asyncio, websockets
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs

async def debug_composer():
    tabs = get_tabs()
    wa = [t for t in tabs if 'web.whatsapp.com' in (t.get('url') or '') and t.get('type') == 'page']
    if not wa:
        print('NO WA TAB')
        return
    ws_url = wa[0]['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
        await ws.recv()
        
        # Find composer and nearby buttons
        find_composer = """
        (() => {
            const composer = document.querySelector('[data-testid="conversation-compose-box-input"]');
            if (!composer) return {composer: null};
            
            // Find all buttons in the main area
            const main = document.querySelector('#main');
            const buttons = main ? [...main.querySelectorAll('button, [role="button"], span[data-icon]')] : [];
            
            return {
                composer: {
                    tag: composer.tagName,
                    class: composer.className,
                    testid: composer.getAttribute('data-testid'),
                    text: (composer.innerText || composer.textContent || '').slice(0,100)
                },
                buttons: buttons.map((b, i) => ({
                    index: i,
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
        await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": find_composer, "awaitPromise": True}}))
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get('id') == 2:
                result = data.get('result', {})
                # The result is an object reference, need to get its value
                obj_id = result.get('result', {}).get('objectId')
                if obj_id:
                    await ws.send(json.dumps({"id": 3, "method": "Runtime.getProperties", "params": {"objectId": obj_id, "ownProperties": True}}))
                    msg2 = await ws.recv()
                    print(f"Composer details: {msg2}")
                break
            elif 'method' in data:
                pass  # Ignore events

asyncio.run(debug_composer())