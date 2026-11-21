import sys, json, time, asyncio, websockets, urllib.request
sys.path.insert(0, '/home/ubuntu')

async def get_eval_result(ws, expr_id, expression):
    await ws.send(json.dumps({"id": expr_id, "method": "Runtime.enable"}))
    await ws.recv()
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

async def send_via_share_page():
    # Find the share page tab
    tabs_list = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/list"))
    share_tab = None
    for t in tabs_list:
        url = t.get('url', '')
        if 'api.whatsapp.com/send' in url and t.get('type') == 'page':
            share_tab = t
            break
    
    if not share_tab:
        print("Share page tab not found")
        return False
    
    print(f"Share tab: {share_tab.get('url')}, WS: {share_tab.get('webSocketDebuggerUrl')}")
    
    async with websockets.connect(share_tab['webSocketDebuggerUrl']) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
        await ws.recv()
        
        # Click "Continue to Chat"
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
        
        # Check if chat opened (might be in a new tab)
        check_main = """
        (() => {
            const main = document.querySelector('#main');
            const composer = document.querySelector('[data-testid="conversation-compose-box-input"]');
            return {main: !!main, composer: !!composer, url: window.location.href};
        })()
        """
        check_result = await get_eval_result(ws, 3, check_main)
        print(f"Check chat: {check_result}")
        
        return True

message = open('/home/ubuntu/shudokan_nudge_wa.txt', encoding='utf-8').read()
asyncio.run(send_via_share_page())
print("Done!")