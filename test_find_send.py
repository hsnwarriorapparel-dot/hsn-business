import sys, json, time, asyncio, websockets
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs

async def debug_send_button():
    tabs = get_tabs()
    wa = [t for t in tabs if 'web.whatsapp.com' in (t.get('url') or '') and t.get('type') == 'page']
    if not wa:
        print('NO WA TAB')
        return
    ws_url = wa[0]['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
        await ws.recv()
        
        # Find send button
        find_send = """
        (() => {
            const btns = [
                document.querySelector('[data-testid="compose-btn-send"]'),
                document.querySelector('[aria-label="Send"]'),
                document.querySelector('span[data-icon="send"]'),
                document.querySelector('button[data-testid="compose-btn-send"]'),
                document.querySelector('div[role="button"][aria-label="Send"]')
            ];
            return btns.map((b, i) => b ? {index: i, tag: b.tagName, class: b.className, aria: b.getAttribute('aria-label'), testid: b.getAttribute('data-testid'), disabled: b.disabled, parent: b.parentElement?.tagName} : null).filter(Boolean);
        })()
        """
        await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": find_send, "awaitPromise": True}}))
        
        # Read responses until we get the result with id=2
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get('id') == 2:
                print(f"Send buttons result: {json.dumps(data.get('result', {}), indent=2)}")
                break
            elif 'method' in data:
                print(f"Event: {data['method']}")

asyncio.run(debug_send_button())