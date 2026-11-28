import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

async def check_restrictions(ws):
    print('=== CHECKING DM RESTRICTIONS ===')
    
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
    
    # Check for restriction messages
    expr_restrict = r'(function() { const allText = document.body.innerText; const lines = allText.split("\n"); const results = []; lines.forEach(l => { const lower = l.toLowerCase(); if (lower.includes("follow") || lower.includes("mutual") || lower.includes("restrict") || lower.includes("cant") || lower.includes("cannot") || lower.includes("unable") || lower.includes("limite") || lower.includes("request") || lower.includes("pending")) { results.push(l.trim()); } }); return JSON.stringify(results); })()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr_restrict, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            results = json.loads(data['result'].get('value', '[]'))
            print(f'  Restriction messages: {results}')
            break
    
    # Check composer state
    expr_composer = r'(function() { const textarea = document.querySelector("div[role=\"textbox\"][contenteditable=\"true\"].xzsf02u"); if (textarea) { const parent = textarea.closest("div[role=\"dialog\"], div[role=\"region\"], form, div"); return JSON.stringify({found: true, parentTag: parent?.tagName, parentClass: parent?.className, textareaClass: textarea.className, placeholder: textarea.getAttribute("placeholder") || ""}); } return {found: false}; })()'
    await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': expr_composer, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 4:
            print(f'  Composer state: {data["result"]["result"]["value"]}')
            break
    
    # Check for any SVG paper plane
    expr_svg = r'(function() { const svgs = document.querySelectorAll("svg"); const results = []; svgs.forEach(s => { const aria = s.getAttribute("aria-label") || ""; const cls = s.className?.baseVal || s.className || ""; if (aria.toLowerCase().includes("send") || aria.toLowerCase().includes("paper") || aria.toLowerCase().includes("plane") || aria.toLowerCase().includes("enviar") || cls.includes("send") || cls.includes("paper")) { results.push({aria, cls, parent: s.parentElement?.tagName, parentClass: s.parentElement?.className}); } }); return JSON.stringify(results); })()'
    await ws.send(json.dumps({'id': 5, 'method': 'Runtime.evaluate', 'params': {'expression': expr_svg, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 5:
            results = json.loads(data['result'].get('value', '[]'))
            print(f'  Paper plane SVGs: {results}')
            break

async def main():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 0, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    await check_restrictions(ws)
    
    await ws.close()

asyncio.run(main())