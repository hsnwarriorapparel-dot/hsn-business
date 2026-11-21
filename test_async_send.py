import sys, json, time, asyncio, websockets
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval, make_cdp

async def send_wa(phone, message):
    tabs = get_tabs()
    wa = [t for t in tabs if 'web.whatsapp.com' in (t.get('url') or '') and t.get('type') == 'page']
    if not wa:
        print('NO WA TAB')
        return False
    ws_url = wa[0]['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url) as ws:
        # Enable Runtime
        await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
        await ws.recv()
        
        # Search for contact
        search_contact = f"""
        (() => {{
            const searchBox = document.querySelector('[data-testid="chat-list-search"]') ||
                             document.querySelector('[aria-label="Search"]') ||
                             document.querySelector('input[type="text"]');
            if (searchBox) {{
                searchBox.focus();
                searchBox.value = '{phone}';
                searchBox.dispatchEvent(new Event('input', {{bubbles: true}}));
                return true;
            }}
            return false;
        }})()
        """
        await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": search_contact, "awaitPromise": True}}))
        result = await ws.recv()
        print(f"Search contact: {result}")
        await asyncio.sleep(3)
        
        # Click on contact - try multiple selectors
        click_contact = """
        (() => {
            const chatItems = document.querySelectorAll('[data-testid^="list-item-"], [data-testid="chat-list-item"], div[role="listitem"], div[role="row"]');
            for (const item of chatItems) {
                const text = (item.innerText || item.textContent || '').toLowerCase();
                if (text.includes('+34 661 57 14 63') || text.includes('34661571463')) {
                    item.scrollIntoView({block: 'center', behavior: 'instant'});
                    item.click();
                    return true;
                }
            }
            return false;
        })()
        """
        await ws.send(json.dumps({"id": 3, "method": "Runtime.evaluate", "params": {"expression": click_contact, "awaitPromise": True}}))
        result = await ws.recv()
        print(f"Click contact: {result}")
        await asyncio.sleep(5)
        
        # Check if conversation opened
        check_open = """
        (() => !!document.querySelector('[data-testid="conversation-compose-box-input"]'))()
        """
        await ws.send(json.dumps({"id": 4, "method": "Runtime.evaluate", "params": {"expression": check_open, "awaitPromise": True}}))
        result = await ws.recv()
        print(f"Check open: {result}")
        
        # If not open, try to check main area
        check_main = """
        (() => ({main: !!document.querySelector('#main'), selected: !!document.querySelector('[aria-selected="true"]')}))()
        """
        await ws.send(json.dumps({"id": 5, "method": "Runtime.evaluate", "params": {"expression": check_main, "awaitPromise": True}}))
        result = await ws.recv()
        print(f"Check main: {result}")
        
        return True

phone = "+34 661 57 14 63"
message = open('/home/ubuntu/shudokan_nudge_wa.txt', encoding='utf-8').read()

asyncio.run(send_wa(phone, message))