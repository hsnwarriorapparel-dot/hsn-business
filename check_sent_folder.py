import asyncio
import websockets
import json

ws_url = 'ws://localhost:9222/devtools/page/B93A66E395208FCD2D9B994E0CCABB9A'

async def check_sent_folder():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    # Navigate to sent folder
    print('1. Navigating to Sent folder...')
    await ws.send(json.dumps({'id': 2, 'method': 'Page.navigate', 'params': {'url': 'https://mail.google.com/mail/u/0/#sent'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            print('Navigate result:', data)
            break
    
    await asyncio.sleep(5)
    
    # Get email list
    print('2. Getting sent emails...')
    expr = r'(function() { const rows = document.querySelectorAll("tr.zA, div[role=\"row\"]"); const emails = []; rows.forEach(r => { const text = r.innerText; if(text.includes("Houston") || text.includes("Starter Kit") || text.includes("Propuesta")) { emails.push(text.substring(0, 200)); } }); return JSON.stringify(emails.slice(0, 10)); })()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
    for _ in range(5):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            print('Sent emails:', data)
            break
    
    await ws.close()

asyncio.run(check_sent_folder())