import asyncio
import websockets
import json

ws_url = 'ws://localhost:9222/devtools/page/B93A66E395208FCD2D9B994E0CCABB9A'

async def debug_gmail_compose():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    # Check current page title and state
    print('1. Checking page state...')
    expr = r'document.title + " | " + document.readyState'
    await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': expr}}))
    for _ in range(5):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            print('Page state:', data)
            break
    
    # Check if compose is already open - look for send button
    print('2. Checking for Send button...')
    expr2 = r'document.querySelector("div[role=\"button\"][aria-label*=\"Send\"]") || document.querySelector("div[data-tooltip*=\"Send\"]")'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr2}}))
    for _ in range(5):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            print('Send button:', data)
            break
    
    # Check for Subject field
    print('3. Checking for Subject field...')
    expr3 = r'document.querySelector("input[name=\"subjectbox\"]") || document.querySelector("input[aria-label*=\"Subject\"]")'
    await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': expr3}}))
    for _ in range(5):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 4:
            print('Subject field:', data)
            break
    
    # Check for Body field
    print('4. Checking for Body field...')
    expr4 = r'document.querySelector("div[role=\"textbox\"][contenteditable=\"true\"]") || document.querySelector("div[aria-label*=\"Message Body\"]")'
    await ws.send(json.dumps({'id': 5, 'method': 'Runtime.evaluate', 'params': {'expression': expr4}}))
    for _ in range(5):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 5:
            print('Body field:', data)
            break
    
    # Try typing in To field (div.afx)
    print('5. Trying to type in To field...')
    expr5 = r'(function() { var el = document.querySelector("div[role=\"listbox\"]"); if(el) { el.click(); return true; } return false; })()'
    await ws.send(json.dumps({'id': 6, 'method': 'Runtime.evaluate', 'params': {'expression': expr5}}))
    for _ in range(5):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 6:
            print('Click To field:', data)
            break
    
    await asyncio.sleep(1)
    
    # Check if input appeared
    print('6. Checking for email input...')
    expr6 = r'document.querySelector("input[aria-label*=\"To\"]") || document.querySelector("textarea[aria-label*=\"To\"]") || document.querySelector("input[data-testid*=\"to\"]")'
    await ws.send(json.dumps({'id': 7, 'method': 'Runtime.evaluate', 'params': {'expression': expr6}}))
    for _ in range(5):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 7:
            print('Email input:', data)
            break
    
    await ws.close()

asyncio.run(debug_gmail_compose())