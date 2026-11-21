import sys, json, time, asyncio, websockets, urllib.request
sys.path.insert(0, '/home/ubuntu')

async def send_to_shudokan(message):
    tabs_list = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/list"))
    target_tab = None
    for t in tabs_list:
        if t.get('title') == '(2) WhatsApp Business' and t.get('type') == 'page':
            target_tab = t
            break
    
    if not target_tab:
        print("Target tab not found")
        return False
    
    print(f"Using tab: {target_tab.get('title')} - {target_tab.get('url')}")
    
    async with websockets.connect(target_tab['webSocketDebuggerUrl']) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
        await ws.recv()
        
        # Click on the Shudokan chat row (+34 661 57 14 63)
        click_expr = """
        (() => {
            // Find the chat row with this phone number
            const rows = document.querySelectorAll('[role="listitem"], [role="row"], [data-testid^="list-item-"]');
            for (const row of rows) {
                const text = row.innerText || row.textContent || '';
                if (text.includes('34661571463') || text.includes('661 57 14 63') || text.includes('661571463')) {
                    console.log('Found chat row:', text.slice(0,100));
                    row.click();
                    return {found: true, text: text.slice(0,100)};
                }
            }
            // Try finding by coordinate click on gridcell
            const cells = document.querySelectorAll('[role="gridcell"]');
            for (const cell of cells) {
                const text = cell.innerText || cell.textContent || '';
                if (text.includes('34661571463') || text.includes('661 57 14 63') || text.includes('661571463')) {
                    console.log('Found gridcell:', text.slice(0,100));
                    cell.click();
                    return {found: true, text: text.slice(0,100)};
                }
            }
            return {found: false};
        })()
        """
        await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": click_expr, "awaitPromise": True}}))
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get('id') == 2:
                result = data.get('result', {}).get('result', {})
                obj_id = result.get('objectId')
                if obj_id:
                    await ws.send(json.dumps({"id": 3, "method": "Runtime.getProperties", "params": {"objectId": obj_id, "ownProperties": True}}))
                    msg2 = await ws.recv()
                    print(f"Click result: {msg2}")
                break
        
        # Wait for chat to open
        await asyncio.sleep(3)
        
        # Check if chat is open
        check_expr = """(() => ({hasMain: !!document.querySelector('#main'), hasComposer: !!document.querySelector('[data-testid=\"conversation-compose-box-input\"]'), title: document.title}))()"""
        await ws.send(json.dumps({"id": 4, "method": "Runtime.evaluate", "params": {"expression": check_expr, "awaitPromise": True}}))
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get('id') == 4:
                result = data.get('result', {}).get('result', {})
                obj_id = result.get('objectId')
                if obj_id:
                    await ws.send(json.dumps({"id": 5, "method": "Runtime.getProperties", "params": {"objectId": obj_id, "ownProperties": True}}))
                    msg2 = await ws.recv()
                    print(f"Check chat: {msg2}")
                break
        
        # If chat is open, send message
        # Type message
        escaped_msg = message.replace('`', '\\`').replace('${', '\\${')
        type_expr = f"""
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
        await ws.send(json.dumps({"id": 6, "method": "Runtime.evaluate", "params": {"expression": type_expr, "awaitPromise": True}}))
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get('id') == 6:
                result = data.get('result', {}).get('result', {})
                obj_id = result.get('objectId')
                if obj_id:
                    await ws.send(json.dumps({"id": 7, "method": "Runtime.getProperties", "params": {"objectId": obj_id, "ownProperties": True}}))
                    msg2 = await ws.recv()
                    print(f"Type result: {msg2}")
                break
        
        await asyncio.sleep(2)
        
        # Click Send
        send_expr = """
        (() => {
            const sendBtn = document.querySelector('[data-testid="compose-btn-send"]') ||
                           document.querySelector('[aria-label="Send"]') ||
                           document.querySelector('span[data-icon="send"]') ||
                           document.querySelector('button[aria-label="Send"]');
            if (sendBtn) {
                sendBtn.click();
                return true;
            }
            return false;
        })()
        """
        await ws.send(json.dumps({"id": 8, "method": "Runtime.evaluate", "params": {"expression": send_expr, "awaitPromise": True}}))
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get('id') == 8:
                result = data.get('result', {}).get('result', {})
                obj_id = result.get('objectId')
                if obj_id:
                    await ws.send(json.dumps({"id": 9, "method": "Runtime.getProperties", "params": {"objectId": obj_id, "ownProperties": True}}))
                    msg2 = await ws.recv()
                    print(f"Send result: {msg2}")
                break
        
        await asyncio.sleep(3)
        return True

message = open('/home/ubuntu/shudokan_nudge_wa.txt', encoding='utf-8').read()
asyncio.run(send_to_shudokan(message))
print("Done!")