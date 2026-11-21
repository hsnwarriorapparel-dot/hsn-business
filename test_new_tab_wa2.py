import sys, json, time, asyncio, websockets, urllib.request
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs

async def get_eval_result(ws, expr_id, expression):
    await ws.send(json.dumps({"id": expr_id, "method": "Runtime.evaluate", "params": {"expression": expression, "awaitPromise": True}}))
    while True:
        msg = await ws.recv()
        data = json.loads(msg)
        if data.get('id') == expr_id:
            result = data.get('result', {}).get('result', {})
            obj_id = result.get('objectId')
            if obj_id:
                await ws.send(json.dumps({"id": expr_id + 100, "method": "Runtime.getProperties", "params": {"objectId": obj_id, "ownProperties": True}}))
                msg2 = await ws.recv()
                data2 = json.loads(msg2)
                props = data2.get('result', {}).get('result', [])
                obj = {}
                for prop in props:
                    val = prop.get('value', {})
                    if val.get('type') in ('string', 'number', 'boolean'):
                        obj[prop['name']] = val.get('value')
                    elif val.get('type') == 'object' and val.get('subtype') == 'null':
                        obj[prop['name']] = None
                    elif val.get('type') == 'object':
                        await ws.send(json.dumps({"id": expr_id + 200, "method": "Runtime.getProperties", "params": {"objectId": val['objectId'], "ownProperties": True}}))
                        msg3 = await ws.recv()
                        data3 = json.loads(msg3)
                        nested_props = data3.get('result', {}).get('result', [])
                        nested_obj = {}
                        for np in nested_props:
                            nv = np.get('value', {})
                            if nv.get('type') in ('string', 'number', 'boolean'):
                                nested_obj[np['name']] = nv.get('value')
                        obj[prop['name']] = nested_obj
                return obj
            else:
                return result.get('value')
        elif 'method' in data:
            continue
    return None

async def send_via_new_tab(phone, message):
    tabs = get_tabs()
    version = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/version"))
    browser_ws_url = version['webSocketDebuggerUrl']
    
    async with websockets.connect(browser_ws_url) as browser_ws:
        clean_phone = phone.replace('+', '').replace(' ', '').replace('-', '')
        await browser_ws.send(json.dumps({"id": 1, "method": "Target.createTarget", "params": {"url": f"https://wa.me/{clean_phone}"}}))
        result = await browser_ws.recv()
        print(f"Create target: {result}")
        data = json.loads(result)
        target_id = data.get('result', {}).get('targetId')
        print(f"Target ID: {target_id}")
        
        # Wait and find new tab
        new_tab = None
        for attempt in range(10):
            await asyncio.sleep(2)
            tabs_list = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/list"))
            for t in tabs_list:
                if t.get('targetId') == target_id:
                    new_tab = t
                    break
            if new_tab:
                break
        
        if not new_tab:
            print("New tab not found after retries")
            return False
        
        print(f"New tab: {new_tab.get('url')}, WS: {new_tab.get('webSocketDebuggerUrl')}")
        
        async with websockets.connect(new_tab['webSocketDebuggerUrl']) as ws:
            await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
            await ws.recv()
            
            await asyncio.sleep(5)
            
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
            result = await get_eval_result(ws, 2, click_continue)
            print(f"Click continue: {result}")
            await asyncio.sleep(5)
            
            check_main = """
            (() => {
                const main = document.querySelector('#main');
                const composer = document.querySelector('[data-testid="conversation-compose-box-input"]');
                return {main: !!main, composer: !!composer};
            })()
            """
            check_result = await get_eval_result(ws, 3, check_main)
            print(f"Check chat: {check_result}")
            
            if check_result and check_result.get('composer'):
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
                result = await get_eval_result(ws, 4, type_message)
                print(f"Type message: {result}")
                await asyncio.sleep(2)
                
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
                result = await get_eval_result(ws, 5, click_send)
                print(f"Click send: {result}")
                await asyncio.sleep(3)
                
                return True
            
            return False

phone = "+34 661 57 14 63"
message = open('/home/ubuntu/shudokan_nudge_wa.txt', encoding='utf-8').read()

print(f"Sending WA via new tab to {phone}")
asyncio.run(send_via_new_tab(phone, message))
print("Done!")