import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

async def debug_dm():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    # Navigate to profile
    print('1. Navigating to /gigears/...')
    await ws.send(json.dumps({'id': 2, 'method': 'Page.navigate', 'params': {'url': 'https://www.instagram.com/gigears/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            break
    
    await asyncio.sleep(5)
    
    # Click Message button
    print('2. Clicking Message button...')
    expr2 = r'(function() { const btns = document.querySelectorAll("button, div[role=\"button\"]"); for (const btn of btns) { const text = (btn.innerText || "").toLowerCase(); if (text === "message") { btn.click(); return {clicked: true, text: btn.innerText}; } } return {clicked: false}; })()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr2, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            print('Message click:', data)
            break
    
    await asyncio.sleep(3)
    
    # Find all textareas and contenteditable divs
    print('3. Finding DM composer inputs...')
    expr3 = r'(function() { const inputs = []; document.querySelectorAll("textarea, div[contenteditable=\"true\"]").forEach(el => { inputs.push({tag: el.tagName, placeholder: el.placeholder || "", class: el.className, role: el.getAttribute("role") || "", ariaLabel: el.getAttribute("aria-label") || ""}); }); return JSON.stringify(inputs); })()'
    await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': expr3, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 4:
            print('DM inputs:', data)
            break
    
    await ws.close()

asyncio.run(debug_dm())