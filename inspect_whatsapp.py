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
    
    # Inspect page
    print("=== WHATSAPP: Page Info ===")
    wa_info = await evaluate(wa_ws, """
    (() => ({
        title: document.title,
        url: window.location.href
    }))()
    """)
    print(json.dumps(wa_info, indent=2))
    
    # Find search box
    print("\n=== WHATSAPP: Find Search/Input Elements ===")
    wa_inputs = await evaluate(wa_ws, """
    (() => {
        const inputs = Array.from(document.querySelectorAll('div[contenteditable="true"], input, textarea'));
        return inputs.map(i => ({
            tag: i.tagName,
            contenteditable: i.getAttribute('contenteditable') || '',
            title: i.getAttribute('title') || '',
            placeholder: i.getAttribute('placeholder') || '',
            dataTab: i.getAttribute('data-tab') || '',
            ariaLabel: i.getAttribute('aria-label') || '',
            class: (i.className || '').slice(0,60),
            visible: i.offsetParent !== null
        })).filter(i => i.visible);
    })()
    """)
    print(json.dumps(wa_inputs, indent=2))
    
    # Find chat list items
    print("\n=== WHATSAPP: Chat List Items ===")
    wa_chats = await evaluate(wa_ws, """
    (() => {
        const chats = Array.from(document.querySelectorAll('div[role="row"], div[role="listitem"], div[tabindex="-1"]'));
        return chats.map(c => ({
            text: c.innerText.trim().slice(0,100),
            class: (c.className || '').slice(0,60),
            visible: c.offsetParent !== null
        })).filter(c => c.visible && c.text.length > 0).slice(0, 20);
    })()
    """)
    print(json.dumps(wa_chats, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
