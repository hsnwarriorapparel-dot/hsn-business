import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

async def try_send_methods(ws):
    print('=== TRYING DIFFERENT SEND METHODS ===')
    
    # Navigate and open DM
    await ws.send(json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': 'https://www.instagram.com/checkmatbristol/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 1:
            break
    
    await asyncio.sleep(4)
    
    # Click Message
    expr_msg = r'(function() { const btns = document.querySelectorAll("button, div[role=\"button\"]"); for (const btn of btns) { const text = (btn.innerText || "").toLowerCase(); if (text === "message") { btn.click(); return {clicked: true}; } } return {clicked: false}; })()'
    await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': expr_msg, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            break
    
    await asyncio.sleep(3)
    
    # Type message
    dm_text = "Test from HSN Warrior Apparels"
    expr_dm = f'(function() {{ const textarea = document.querySelector("div[role=\\"textbox\\"][contenteditable=\\"true\\"].xzsf02u"); if (textarea) {{ textarea.focus(); textarea.innerText = `{dm_text.replace("`", "\\\\`").replace("${", "\\\\${")}`; textarea.dispatchEvent(new Event("input", {{bubbles: true}})); return true; }} return false; }})()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr_dm, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            print(f'  Typed: {data["result"]["result"]["value"]}')
            break
    
    await asyncio.sleep(2)
    
    # Method 1: Try plain Enter key
    print('  Method 1: Plain Enter...')
    expr_enter = r'(function() { const textarea = document.querySelector("div[role=\"textbox\"][contenteditable=\"true\"].xzsf02u"); if (textarea) { textarea.focus(); textarea.dispatchEvent(new KeyboardEvent("keydown", {key: "Enter", bubbles: true})); textarea.dispatchEvent(new KeyboardEvent("keyup", {key: "Enter", bubbles: true})); return true; } return false; })()'
    await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': expr_enter, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 4:
            print(f'    Result: {data["result"]["result"]["value"]}')
            break
    
    await asyncio.sleep(3)
    
    # Check if message sent
    expr_check = r'(function() { const allText = document.body.innerText; return allText.includes("Test from HSN Warrior Apparels"); })()'
    await ws.send(json.dumps({'id': 5, 'method': 'Runtime.evaluate', 'params': {'expression': expr_check, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 5:
            print(f'  Message in DOM: {data["result"]["result"]["value"]}')
            break
    
    # Method 2: Try to find Send in portals
    print('  Method 2: Search all portals/modals...')
    expr_portals = r'(function() { const all = document.querySelectorAll("*"); const results = []; all.forEach(el => { const aria = el.getAttribute("aria-label") || ""; const cls = el.className || ""; if ((aria.toLowerCase().includes("send") || aria.toLowerCase().includes("enviar")) && el.offsetWidth > 0) { results.push({tag: el.tagName, aria, cls, rect: el.getBoundingClientRect()}); } }); return JSON.stringify(results); })()'
    await ws.send(json.dumps({'id': 6, 'method': 'Runtime.evaluate', 'params': {'expression': expr_portals, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 6:
            results = json.loads(data['result'].get('value', '[]'))
            print(f'    Send buttons in portals: {results}')
            break

async def main():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 0, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    await try_send_methods(ws)
    
    await ws.close()

asyncio.run(main())