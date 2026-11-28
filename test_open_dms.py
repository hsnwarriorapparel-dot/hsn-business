import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

# Profiles that explicitly invite DMs
TEST_PROFILES = [
    'the47bjjcoop',
    'kuzushi_bjj_dinslaken',
    'funk.jitsu',
    'sanlorenzojiujitsu',
    'rolldeepacademy',
    'bbjja_team',
    'josh_doesbjj',
    'hanisbjj',
    'albjjona',
    '5fifty5bjj',
]

async def test_dm_open(ws, handle):
    print(f'\n=== @{handle} ===')
    
    await ws.send(json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': f'https://www.instagram.com/{handle}/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 1:
            break
    
    await asyncio.sleep(5)
    
    # Check if Message button exists
    expr_msg = r'(function() { const btns = document.querySelectorAll("button, div[role=\"button\"]"); for (const btn of btns) { const text = (btn.innerText || "").toLowerCase(); if (text === "message") { return {found: true, text: btn.innerText}; } } return {found: false}; })()'
    await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': expr_msg, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            msg_result = data['result']['result']['value']
            print(f'  Message button: {msg_result}')
            break
    
    # Check follow status
    expr_follow = r'(function() { const btns = document.querySelectorAll("button"); for (const btn of btns) { const text = (btn.innerText || "").toLowerCase(); if (text === "follow" || text === "following" || text === "requested" || text === "seguir") { return {text: btn.innerText}; } } return {text: "not found"}; })()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr_follow, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            print(f'  Follow status: {data["result"]["result"]["value"]}')
            break
    
    if msg_result.get('found'):
        # Try to open DM and check for Send button
        await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': expr_msg, 'returnByValue': True}}))
        for _ in range(10):
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 4:
                break
        
        await asyncio.sleep(3)
        
        # Check for Send button in composer
        expr_send = r'(function() { const all = document.querySelectorAll("*"); const results = []; all.forEach(el => { const aria = el.getAttribute("aria-label") || ""; const text = (el.innerText || "").trim(); if ((aria.toLowerCase().includes("send") || aria.toLowerCase().includes("enviar") || text === "Send" || text === "Enviar") && el.offsetWidth > 0) { results.push({tag: el.tagName, aria, text, class: el.className}); } }); return JSON.stringify(results); })()'
        await ws.send(json.dumps({'id': 5, 'method': 'Runtime.evaluate', 'params': {'expression': expr_send, 'returnByValue': True}}))
        for _ in range(10):
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 5:
                results = json.loads(data['result'].get('value', '[]'))
                print(f'  Send button: {results}')
                break
        
        return msg_result.get('found'), results
    
    return False, []

async def main():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 0, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    open_dms = []
    for handle in TEST_PROFILES:
        has_msg, send_btns = await test_dm_open(ws, handle)
        if has_msg and send_btns:
            open_dms.append({'handle': handle, 'send_btns': send_btns})
            print(f'  >>> OPEN DM WITH SEND BUTTON: @{handle}')
        await asyncio.sleep(2)
    
    print(f'\n=== OPEN DM PROFILES: {len(open_dms)} ===')
    for d in open_dms:
        print(f'  @{d["handle"]}: {d["send_btns"]}')
    
    await ws.close()

asyncio.run(main())