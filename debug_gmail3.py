import asyncio
import websockets
import json

ws_url = 'ws://localhost:9222/devtools/page/B93A66E395208FCD2D9B994E0CCABB9A'

async def debug_gmail_attrs():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    # Get the To field element and its attributes
    print('1. Getting To field element...')
    expr = r'(function() { var el = document.querySelector("div[role=\"listbox\"]"); if(el) { var attrs = {}; for(var i=0; i<el.attributes.length; i++) { attrs[el.attributes[i].name] = el.attributes[i].value; } return {tag: el.tagName, class: el.className, attrs: attrs, innerHTML: el.innerHTML.substring(0,200)}; } return null; })()'
    await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': expr}}))
    for _ in range(5):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            print('To field attrs:', data)
            break
    
    # Get the email input after click
    print('2. Clicking To field...')
    expr2 = r'(function() { var el = document.querySelector("div[role=\"listbox\"]"); if(el) { el.click(); return true; } return false; })()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr2}}))
    for _ in range(5):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            print('Click result:', data)
            break
    
    await asyncio.sleep(1)
    
    # Get the email input element
    print('3. Getting email input...')
    expr3 = r'(function() { var el = document.querySelector("input[aria-label*=\"To\" i]") || document.querySelector("input[role=\"combobox\"]") || document.querySelector("div[role=\"textbox\"][aria-label*=\"To\" i]") || document.querySelector("input#:tt"); if(el) { var attrs = {}; for(var i=0; i<el.attributes.length; i++) { attrs[el.attributes[i].name] = el.attributes[i].value; } return {tag: el.tagName, class: el.className, attrs: attrs, value: el.value}; } return null; })()'
    await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': expr3}}))
    for _ in range(5):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 4:
            print('Email input attrs:', data)
            break
    
    await ws.close()

asyncio.run(debug_gmail_attrs())