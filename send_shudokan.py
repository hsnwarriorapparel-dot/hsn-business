import asyncio
import json
import websockets

async def send_cdp(ws_url, method, params=None):
    async with websockets.connect(ws_url) as ws:
        req = {"id": 1, "method": method, "params": params or {}}
        await ws.send(json.dumps(req))
        resp = await ws.recv()
        return json.loads(resp)

async def main():
    # Instagram tab
    ig_ws = "ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC"
    # WhatsApp tab
    wa_ws = "ws://127.0.0.1:9222/devtools/page/93073410C8FA7BC7FB363FD9EC35BD7E"
    
    # Enable Runtime domain for both
    for ws in [ig_ws, wa_ws]:
        await send_cdp(ws, "Runtime.enable")
        print(f"Enabled Runtime on {ws}")
    
    # Get Instagram document to find Shudokan chat
    ig_result = await send_cdp(ig_ws, "Runtime.evaluate", {
        "expression": "document.title + ' | ' + document.URL",
        "returnByValue": True
    })
    print(f"Instagram page: {ig_result}")

if __name__ == "__main__":
    asyncio.run(main())
