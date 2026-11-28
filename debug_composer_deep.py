import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

async def debug_composer(ws):
    print('=== DEBUGGING DM COMPOSER ON @checkmatbristol ===')
    
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
    dm_text = "Test message from HSN Warrior Apparels"
    expr_dm = f'(function() {{ const textarea = document.querySelector("div[role=\\"textbox\\"][contenteditable=\\"true\\"].xzsf02u"); if (textarea) {{ textarea.focus(); textarea.innerText = `{dm_text.replace("`", "\\\\`").replace("${", "\\\\${")}`; textarea.dispatchEvent(new Event("input", {{bubbles: true}})); return true; }} return false; }})()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr_dm, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            print(f'  Typed: {data["result"]["result"]["value"]}')
            break
    
    await asyncio.sleep(1)
    
    # Deep search for Send button - check all elements with SVG, aria-label, etc.
    expr_deep = r'(function() { const all = document.querySelectorAll("*"); const results = []; all.forEach(el => { const aria = el.getAttribute("aria-label") || ""; const title = el.getAttribute("title") || ""; const text = (el.innerText || "").trim(); const cls = el.className || ""; const tag = el.tagName; if ((aria.toLowerCase().includes("send") || aria.toLowerCase().includes("enviar") || title.toLowerCase().includes("send") || title.toLowerCase().includes("enviar") || cls.includes("send") || tag === "SVG" || (text && (text === "Send" || text === "Enviar"))) && (el.offsetWidth > 0 || el.offsetHeight > 0)) { results.push({tag, aria, title, text, cls, visible: el.offsetWidth > 0 && el.offsetHeight > 0}); } }); return JSON.stringify(results); })()'
    await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': expr_deep, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 4:
            results = json.loads(data['result'].get('value', '[]'))
            print(f'  Send candidates ({len(results)}):')
            for r in results:
                print(f'    {r}')
            break
    
    # Also check for the specific Send button div with role=button
    expr_send_div = r'(function() { const divs = document.querySelectorAll("div[role=\"button\"]"); const results = []; divs.forEach(d => { const aria = d.getAttribute("aria-label") || ""; const text = (d.innerText || "").trim(); const cls = d.className || ""; if (aria.toLowerCase().includes("send") || aria.toLowerCase().includes("enviar")) { results.push({aria, text, cls, children: d.children.length}); } }); return JSON.stringify(results); })()'
    await ws.send(json.dumps({'id': 5, 'method': 'Runtime.evaluate', 'params': {'expression': expr_send_div, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 5:
            results = json.loads(data['result'].get('value', '[]'))
            print(f'  Div[role=button] with send aria: {results}')
            break

async def main():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 0, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    await debug_composer(ws)
    
    await ws.close()

asyncio.run(main())