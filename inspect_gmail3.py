import asyncio
import json
import websockets
import aiohttp

async def get_gmail_ws():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://127.0.0.1:9222/json') as resp:
            pages = await resp.json()
            for p in pages:
                if 'mail.google.com' in p.get('url', ''):
                    return p.get('webSocketDebuggerUrl')
    return None

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
    gmail_ws = await get_gmail_ws()
    
    if not gmail_ws:
        print("Gmail tab not found")
        return
    
    print(f"Gmail WS: {gmail_ws}")
    await send_cdp(gmail_ws, "Runtime.enable")
    
    # Check page title and URL
    print("=== GMAIL: Page Info ===")
    gm_info = await evaluate(gmail_ws, """
    (() => ({
        title: document.title,
        url: window.location.href,
        readyState: document.readyState
    }))()
    """)
    print(json.dumps(gm_info, indent=2))
    
    # Check all divs with text
    print("\n=== GMAIL: All Divs with Text ===")
    gm_divs = await evaluate(gmail_ws, """
    (() => {
        const divs = Array.from(document.querySelectorAll('div'));
        return divs.map(d => d.innerText.trim()).filter(t => t.length > 5 && t.length < 100).slice(0, 50);
    })()
    """)
    print(json.dumps(gm_divs, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
