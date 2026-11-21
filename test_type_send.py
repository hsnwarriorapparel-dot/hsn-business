import sys, json, time, asyncio, websockets, urllib.request
sys.path.insert(0, '/home/ubuntu')

async def send_message_now(message):
    tabs_list = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/list"))
    target_tab = None
    for t in tabs_list:
        if t.get('title') == '(2) WhatsApp Business' and t.get('type') == 'page':
            target_tab = t
            break
    
    if not target_tab:
        print("Target tab not found")
        return False
    
    print(f"Using tab: {target_tab.get('title')}")
    
    async with websockets.connect(target_tab['webSocketDebuggerUrl']) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
        await ws.recv()
        
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
        await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": type_expr, "awaitPromise": True}}))
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get('id') == 2:
                result = data.get('result', {}).get('result', {})
                obj_id = result.get('objectId')
                if obj_id:
                    await ws.send(json.dumps({"id": 3, "method": "Runtime.getProperties", "params": {"objectId": obj_id, "ownProperties": True}}))
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
        await ws.send(json.dumps({"id": 4, "method": "Runtime.evaluate", "params": {"expression": send_expr, "awaitPromise": True}}))
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get('id') == 4:
                result = data.get('result', {}).get('result', {})
                obj_id = result.get('objectId')
                if obj_id:
                    await ws.send(json.dumps({"id": 5, "method": "Runtime.getProperties", "params": {"objectId": obj_id, "ownProperties": True}}))
                    msg2 = await ws.recv()
                    print(f"Send result: {msg2}")
                break
        
        await asyncio.sleep(3)
        return True

message = open('/home/ubuntu/shudokan_nudge_wa.txt', encoding='utf-8').read()
asyncio.run(send_message_now(message))
print("Done!")