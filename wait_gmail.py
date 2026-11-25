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
    
    # Navigate to Gmail basic HTML (might bypass cookie rotation)
    print("=== GMAIL: Navigate to Basic HTML ===")
    await evaluate(gmail_ws, """
    (() => {
        window.location.href = 'https://mail.google.com/mail/u/0/h/';
        return 'navigated';
    })()
    """)
    print("Navigation triggered")
    await asyncio.sleep(8)
    
    # Re-get WebSocket URL
    gmail_ws = await get_gmail_ws()
    if not gmail_ws:
        print("Gmail tab lost")
        return
    
    print(f"New Gmail WS: {gmail_ws}")
    await send_cdp(gmail_ws, "Runtime.enable")
    
    # Check page
    gm_info = await evaluate(gmail_ws, """
    (() => ({
        title: document.title,
        url: window.location.href
    }))()
    """)
    print(f"Page: {json.dumps(gm_info, indent=2)}")
    
    # Find compose
    gm_compose = await evaluate(gmail_ws, """
    (() => {
        const elements = Array.from(document.querySelectorAll('a, button, input, [onclick]'));
        return elements.map(el => ({
            tag: el.tagName,
            href: el.getAttribute('href') || '',
            onclick: el.getAttribute('onclick') || '',
            text: el.innerText.trim().slice(0,50),
            class: (el.className || '').slice(0,60)
        })).filter(e => e.href.includes('compose') || e.text.toLowerCase().includes('compose') || e.text.toLowerCase().includes('redactar')).slice(0, 20);
    })()
    """)
    print(f"Compose links: {json.dumps(gm_compose, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
