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
    
    # Instagram: Get all visible text elements in DM inbox
    print("=== INSTAGRAM DOM ===")
    ig_dom = await evaluate(ig_ws, """
    (() => {
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        const texts = [];
        while (walker.nextNode()) {
            const t = walker.currentNode.textContent.trim();
            if (t.length > 2 && t.length < 100) texts.push(t);
        }
        return [...new Set(texts)].slice(0, 50);
    })()
    """)
    print(json.dumps(ig_dom, indent=2))
    
    # WhatsApp: Get all visible text elements
    print("\n=== WHATSAPP DOM ===")
    wa_dom = await evaluate(wa_ws, """
    (() => {
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        const texts = [];
        while (walker.nextNode()) {
            const t = walker.currentNode.textContent.trim();
            if (t.length > 2 && t.length < 100) texts.push(t);
        }
        return [...new Set(texts)].slice(0, 50);
    })()
    """)
    print(json.dumps(wa_dom, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
