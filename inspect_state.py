import asyncio
import json
import websockets

async def send_cdp(ws_url, method, params=None):
    async with websockets.connect(ws_url) as ws:
        req = {"id": 1, "method": method, "params": params or {}}
        await ws.send(json.dumps(req))
        resp = await ws.recv()
        return json.loads(resp)

async def evaluate(ws_url, expression, return_by_value=True):
    return await send_cdp(ws_url, "Runtime.evaluate", {
        "expression": expression,
        "returnByValue": return_by_value,
        "awaitPromise": True
    })

async def main():
    ig_ws = "ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC"
    wa_ws = "ws://127.0.0.1:9222/devtools/page/93073410C8FA7BC7FB363FD9EC35BD7E"
    
    for ws in [ig_ws, wa_ws]:
        await send_cdp(ws, "Runtime.enable")
    
    # Instagram: Check current state
    print("=== INSTAGRAM: Current State ===")
    ig_state = await evaluate(ig_ws, """
    (() => {
        const buttons = Array.from(document.querySelectorAll('button, div[role="button"]'));
        const inputs = Array.from(document.querySelectorAll('textarea, input, div[contenteditable="true"]'));
        return {
            buttons: buttons.map(b => ({text: b.innerText.trim().slice(0,50), aria: b.getAttribute('aria-label')||'', class: b.className.slice(0,40)})).filter(b => b.text),
            inputs: inputs.map(i => ({tag: i.tagName, placeholder: i.getAttribute('placeholder')||'', aria: i.getAttribute('aria-label')||'', role: i.getAttribute('role')||'', class: i.className.slice(0,40)})).filter(i => i.placeholder || i.aria || i.role)
        };
    })()
    """)
    print(json.dumps(ig_state, indent=2))
    
    # WhatsApp: Check current state
    print("\n=== WHATSAPP: Current State ===")
    wa_state = await evaluate(wa_ws, """
    (() => {
        const buttons = Array.from(document.querySelectorAll('button, div[role="button"]'));
        const inputs = Array.from(document.querySelectorAll('input, div[contenteditable="true"]'));
        return {
            buttons: buttons.map(b => ({text: b.innerText.trim().slice(0,50), aria: b.getAttribute('aria-label')||'', class: b.className.slice(0,40)})).filter(b => b.text),
            inputs: inputs.map(i => ({tag: i.tagName, placeholder: i.getAttribute('placeholder')||'', aria: i.getAttribute('aria-label')||'', role: i.getAttribute('role')||'', 'data-tab': i.getAttribute('data-tab')||'', class: i.className.slice(0,40)})).filter(i => i.placeholder || i.aria || i.role || i['data-tab'])
        };
    })()
    """)
    print(json.dumps(wa_state, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
