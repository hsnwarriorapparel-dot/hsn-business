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
    
    # Instagram: Get all clickable elements after "New message"
    print("=== INSTAGRAM: After New Message Click ===")
    ig_elements = await evaluate(ig_ws, """
    (() => {
        const elements = Array.from(document.querySelectorAll('button, div[role="button"], a[role="button"], [role="option"], [tabindex="0"]'));
        return elements.map(e => ({
            tag: e.tagName,
            text: e.innerText.trim().slice(0, 80),
            aria: e.getAttribute('aria-label') || '',
            role: e.getAttribute('role') || '',
            class: e.className.slice(0, 50)
        })).filter(e => e.text.length > 0).slice(0, 30);
    })()
    """)
    print(json.dumps(ig_elements, indent=2))
    
    # WhatsApp: Get chat list after search
    print("\n=== WHATSAPP: After Search ===")
    wa_elements = await evaluate(wa_ws, """
    (() => {
        const elements = Array.from(document.querySelectorAll('[role="listitem"], [role="button"][tabindex], div[tabindex="-1"], ._ak8l, ._ak8o'));
        return elements.map(e => ({
            tag: e.tagName,
            text: e.innerText.trim().slice(0, 100),
            class: e.className.slice(0, 50)
        })).filter(e => e.text.length > 0).slice(0, 20);
    })()
    """)
    print(json.dumps(wa_elements, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
