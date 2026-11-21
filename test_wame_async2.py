import sys, json, time, asyncio, websockets
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs

async def send_via_wame(phone, message):
    tabs = get_tabs()
    wa = [t for t in tabs if 'web.whatsapp.com' in (t.get('url') or '') and t.get('type') == 'page']
    if not wa:
        print('NO WA TAB')
        return False
    ws_url = wa[0]['webSocketDebuggerUrl']
    
    async with websockets.connect(ws_url) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
        await ws.recv()
        
        # Navigate to wa.me link
        clean_phone = phone.replace('+', '').replace(' ', '').replace('-', '')
        navigate_expr = f"window.location.href = 'https://wa.me/{clean_phone}'; true"
        await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": navigate_expr, "awaitPromise": True, "returnByValue": True}}))
        result = await ws.recv()
        print(f"Navigate: {result}")
        await asyncio.sleep(5)
        
        # Click "Continue to Chat" if on landing page
        click_continue = """
        (() => {
            const links = [...document.querySelectorAll('a[href*="web.whatsapp.com"], a[href*="wa.me"]')];
            for (const link of links) {
                const text = (link.innerText || link.textContent || '').toLowerCase();
                if (text.includes('continue') || text.includes('chat') || text.includes('open')) {
                    link.click();
                    return true;
                }
            }
            const buttons = [...document.querySelectorAll('button, [role="button"]')];
            for (const btn of buttons) {
                const text = (btn.innerText || btn.textContent || '').toLowerCase();
                if (text.includes('continue') || text.includes('chat') || text.includes('open')) {
                    btn.click();
                    return true;
                }
            }
            return false;
        })()
        """
        await ws.send(json.dumps({"id": 3, "method": "Runtime.evaluate", "params": {"expression": click_continue, "awaitPromise": True, "returnByValue": True}}))
        result = await ws.recv()
        data = json.loads(result)
        value = data.get('result', {}).get('result', {}).get('value')
        print(f"Click continue: {value}")
        await asyncio.sleep(5)
        
        # Check if chat opened
        check_main = """
        (() => {
            const main = document.querySelector('#main');
            const composer = document.querySelector('[data-testid="conversation-compose-box-input"]');
            return {main: !!main, composer: !!composer};
        })()
        """
        await ws.send(json.dumps({"id": 4, "method": "Runtime.evaluate", "params": {"expression": check_main, "awaitPromise": True, "returnByValue": True}}))
        result = await ws.recv()
        data = json.loads(result)
        result_obj = data.get('result', {}).get('result', {})
        value = result_obj.get('value')
        print(f"Check chat raw: {result_obj}")
        print(f"Check chat value: {value}")
        
        # Handle both string and object return
        if isinstance(value, str):
            try:
                check_result = json.loads(value)
            except:
                check_result = {'main': False, 'composer': False}
        else:
            check_result = value
        
        print(f"Check chat parsed: {check_result}")
        
        if check_result and check_result.get('composer'):
            # Type message
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
            await ws.send(json.dumps({"id": 5, "method": "Runtime.evaluate", "params": {"expression": type_message, "awaitPromise": True, "returnByValue": True}}))
            result = await ws.recv()
            data = json.loads(result)
            value = data.get('result', {}).get('result', {}).get('value')
            print(f"Type message: {value}")
            await asyncio.sleep(2)
            
            # Click Send
            click_send = """
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
            await ws.send(json.dumps({"id": 6, "method": "Runtime.evaluate", "params": {"expression": click_send, "awaitPromise": True, "returnByValue": True}}))
            result = await ws.recv()
            data = json.loads(result)
            value = data.get('result', {}).get('result', {}).get('value')
            print(f"Click send: {value}")
            await asyncio.sleep(3)
            
            return True
        
        return False

phone = "+34 661 57 14 63"
message = open('/home/ubuntu/shudokan_nudge_wa.txt', encoding='utf-8').read()

print(f"Sending WA via wa.me to {phone}")
asyncio.run(send_via_wame(phone, message))
print("Done!")