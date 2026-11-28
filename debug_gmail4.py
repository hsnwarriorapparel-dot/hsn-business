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
    expr = r'(function() { var el = document.querySelector("div[role=\"listbox\"]"); if(el) { var attrs = {}; for(var i=0; i<el.attributes.length; i++) { attrs[el.attributes[i].name] = el.attributes[i].value; } return JSON.stringify({tag: el.tagName, class: el.className, attrs: attrs, innerHTML: el.innerHTML.substring(0,200)}); } return null; })()'
    await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
    for _ in range(5):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            print('To field attrs:', data)
            break
    
    # Get the email input after click
    print('2. Clicking To field...')
    expr2 = r'(function() { var el = document.querySelector("div[role=\"listbox\"]"); if(el) { el.click(); return true; } return false; })()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr2, 'returnByValue': True}}))
    for _ in range(5):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            print('Click result:', data)
            break
    
    await asyncio.sleep(1)
    
    # Get the email input element
    print('3. Getting email input...')
    expr3 = r'(function() { var el = document.querySelector("input[aria-label*=\"To\" i]") || document.querySelector("input[role=\"combobox\"]") || document.querySelector("div[role=\"textbox\"][aria-label*=\"To\" i]") || document.querySelector("input#:tt"); if(el) { var attrs = {}; for(var i=0; i<el.attributes.length; i++) { attrs[el.attributes[i].name] = el.attributes[i].value; } return JSON.stringify({tag: el.tagName, class: el.className, attrs: attrs, value: el.value}); } return null; })()'
    await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': expr3, 'returnByValue': True}}))
    for _ in range(5):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 4:
            print('Email input attrs:', data)
            break
    
    # Get Subject field
    print('4. Getting Subject field...')
    expr4 = r'(function() { var el = document.querySelector("input[name=\"subjectbox\"]") || document.querySelector("input[aria-label*=\"Subject\" i]"); if(el) { var attrs = {}; for(var i=0; i<el.attributes.length; i++) { attrs[el.attributes[i].name] = el.attributes[i].value; } return JSON.stringify({tag: el.tagName, class: el.className, attrs: attrs, value: el.value}); } return null; })()'
    await ws.send(json.dumps({'id': 5, 'method': 'Runtime.evaluate', 'params': {'expression': expr4, 'returnByValue': True}}))
    for _ in range(5):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 5:
            print('Subject field attrs:', data)
            break
    
    # Get Body field
    print('5. Getting Body field...')
    expr5 = r'(function() { var el = document.querySelector("div[role=\"textbox\"][contenteditable=\"true\"]") || document.querySelector("div.Am.Al.editable") || document.querySelector("div[aria-label*=\"Message Body\" i][contenteditable=\"true\"]"); if(el) { var attrs = {}; for(var i=0; i<el.attributes.length; i++) { attrs[el.attributes[i].name] = el.attributes[i].value; } return JSON.stringify({tag: el.tagName, class: el.className, attrs: attrs, innerText: el.innerText.substring(0,100)}); } return null; })()'
    await ws.send(json.dumps({'id': 6, 'method': 'Runtime.evaluate', 'params': {'expression': expr5, 'returnByValue': True}}))
    for _ in range(5):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 6:
            print('Body field attrs:', data)
            break
    
    # Get Send button
    print('6. Getting Send button...')
    expr6 = r'(function() { var el = document.querySelector("div[role=\"button\"][aria-label*=\"Send\" i]") || document.querySelector("button[aria-label*=\"Send\" i]"); if(el) { var attrs = {}; for(var i=0; i<el.attributes.length; i++) { attrs[el.attributes[i].name] = el.attributes[i].value; } return JSON.stringify({tag: el.tagName, class: el.className, attrs: attrs}); } return null; })()'
    await ws.send(json.dumps({'id': 7, 'method': 'Runtime.evaluate', 'params': {'expression': expr6, 'returnByValue': True}}))
    for _ in range(5):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 7:
            print('Send button attrs:', data)
            break
    
    await ws.close()

asyncio.run(debug_gmail_attrs())