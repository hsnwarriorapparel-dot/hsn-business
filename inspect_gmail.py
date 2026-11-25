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
    
    # Inspect compose button
    print("=== GMAIL: Find Compose Button ===")
    gm_compose = await evaluate(gmail_ws, """
    (() => {
        const buttons = Array.from(document.querySelectorAll('div[role="button"], button'));
        return buttons.map(b => ({
            aria: b.getAttribute('aria-label') || '',
            text: b.innerText.trim().slice(0,50),
            class: (b.className || '').slice(0,60)
        })).filter(b => b.aria || b.text).slice(0, 30);
    })()
    """)
    print(json.dumps(gm_compose, indent=2))
    
    # Check for existing compose window
    print("\n=== GMAIL: Check for Compose Window ===")
    gm_window = await evaluate(gmail_ws, """
    (() => {
        const divs = Array.from(document.querySelectorAll('div[role="dialog"], div[aria-label*="Compose"], div[aria-label*="Redactar"]'));
        return divs.map(d => ({
            aria: d.getAttribute('aria-label') || '',
            class: (d.className || '').slice(0,60),
            visible: d.offsetParent !== null
        })).filter(d => d.visible);
    })()
    """)
    print(json.dumps(gm_window, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
