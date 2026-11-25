import asyncio
import json
import websockets
import aiohttp

async def get_wa_ws():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://127.0.0.1:9222/json') as resp:
            pages = await resp.json()
            for p in pages:
                if 'web.whatsapp.com' in p.get('url', ''):
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
    wa_ws = await get_wa_ws()
    
    if not wa_ws:
        print("WhatsApp tab not found")
        return
    
    print(f"WhatsApp WS: {wa_ws}")
    await send_cdp(wa_ws, "Runtime.enable")
    
    # Search and check all results
    print("=== WHATSAPP: Search and Show All Results ===")
    wa_search = await evaluate(wa_ws, """
    (() => {
        const searchBox = document.querySelector('input[aria-label="Search or start a new chat"]');
        if (searchBox) {
            searchBox.focus();
            searchBox.value = '+34 661 571 463';
            searchBox.dispatchEvent(new Event('input', {bubbles: true}));
            return 'searched';
        }
        return 'no_search_box';
    })()
    """)
    print(f"Search: {wa_search}")
    await asyncio.sleep(3)
    
    # Show ALL visible chat list items after search
    wa_all = await evaluate(wa_ws, """
    (() => {
        const chats = Array.from(document.querySelectorAll('div[role="row"], div[role="listitem"], div._ak8l, div[tabindex="-1"]'));
        return chats.map(c => ({
            text: c.innerText.trim().slice(0,150),
            class: (c.className || '').slice(0,80),
            visible: c.offsetParent !== null
        })).filter(c => c.visible).slice(0, 30);
    })()
    """)
    print(json.dumps(wa_all, indent=2))
    
    # Look for "New chat" or similar for the searched number
    wa_new = await evaluate(wa_ws, """
    (() => {
        const buttons = Array.from(document.querySelectorAll('div[role="button"], button, a'));
        return buttons.map(b => ({
            text: b.innerText.trim().slice(0,100),
            aria: b.getAttribute('aria-label') || '',
            class: (b.className || '').slice(0,60)
        })).filter(b => b.text.toLowerCase().includes('new') || b.text.toLowerCase().includes('message') || b.aria.toLowerCase().includes('new') || b.aria.toLowerCase().includes('message')).slice(0, 20);
    })()
    """)
    print(f"New/Message buttons: {json.dumps(wa_new, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
