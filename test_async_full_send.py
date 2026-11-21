import sys, json, time, asyncio, websockets
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs

async def send_wa_full(phone, message):
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
        
        # Click on contact
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
        
        # Type message
        # Escape message for JS template literal
        escaped_msg = message.replace('`', '\\`').replace('${', '\\${')
        type_message = f"""
        (() => {{
            const msgInput = document.querySelector('[data-testid="conversation-compose-box-input"]') ||
                            document.querySelector('[aria-label="Type a message"]') ||
                            document.querySelector('div[contenteditable="true"][data-tab="10"]');
            if (msgInput) {{
                msgInput.focus();
                msgInput.innerText = `{escaped_msg}`;
                msgInput.dispatchEvent(new Event('input', {{bubbles: true}}));
                return true;
            }}
            return false;
        }})()
        """
        await ws.send(json.dumps({"id": 5, "method": "Runtime.evaluate", "params": {"expression": type_message, "awaitPromise": True}}))
        result = await ws.recv()
        print(f"Type message: {result}")
        await asyncio.sleep(2)
        
        # Click Send
        click_send = """
        (() => {
            const sendBtn = document.querySelector('[data-testid="compose-btn-send"]') ||
                           document.querySelector('[aria-label="Send"]') ||
                           document.querySelector('span[data-icon="send"]');
            if (sendBtn) {
                sendBtn.click();
                return true;
            }
            return false;
        })()
        """
        await ws.send(json.dumps({"id": 6, "method": "Runtime.evaluate", "params": {"expression": click_send, "awaitPromise": True}}))
        result = await ws.recv()
        print(f"Click send: {result}")
        await asyncio.sleep(3)
        
        # Verify sent
        verify = """
        (() => {
            const inp = document.querySelector('[data-testid="conversation-compose-box-input"]');
            const v = inp ? (inp.innerText || inp.textContent || '') : '';
            return {composerEmpty: v.trim().length === 0};
        })()
        """
        await ws.send(json.dumps({"id": 7, "method": "Runtime.evaluate", "params": {"expression": verify, "awaitPromise": True}}))
        result = await ws.recv()
        print(f"Verify: {result}")
        
        return True

phone = "+34 661 57 14 63"
message = open('/home/ubuntu/shudokan_nudge_wa.txt', encoding='utf-8').read()

print(f"Sending WA to {phone}")
print(f"Message length: {len(message)}")
asyncio.run(send_wa_full(phone, message))
print("Done!")