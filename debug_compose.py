import asyncio
import websockets
import json

ws_url = 'ws://localhost:9222/devtools/page/B93A66E395208FCD2D9B994E0CCABB9A'

async def debug_compose():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    # Navigate to inbox first
    print('1. Navigating to inbox...')
    await ws.send(json.dumps({'id': 2, 'method': 'Page.navigate', 'params': {'url': 'https://mail.google.com/mail/u/0/#inbox'}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            print('Navigate result:', data)
            break
    
    await asyncio.sleep(3)
    
    # Get Compose button
    print('2. Getting Compose button...')
    expr = r'(function() { var btn = document.querySelector("div[role=\"button\"][aria-label*=\"Compose\" i]") || document.querySelector("div[role=\"button\"][aria-label*=\"Redactar\" i]") || document.querySelector("div[role=\"button\"][aria-label*=\"Schreiben\" i]") || document.querySelector("div.T-I.T-I-KE.L3") || document.querySelector("div[gh=\"cm\"]"); if(btn) { var attrs = {}; for(var i=0; i<btn.attributes.length; i++) { attrs[btn.attributes[i].name] = btn.attributes[i].value; } return JSON.stringify({tag: btn.tagName, class: btn.className, attrs: attrs, innerText: btn.innerText}); } return null; })()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
    for _ in range(5):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            print('Compose button attrs:', data)
            break
    
    await ws.close()

asyncio.run(debug_compose())