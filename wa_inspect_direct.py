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
    
    # Inspect page after direct URL
    print("=== WHATSAPP: Inspect Direct URL Page ===")
    wa_page = await evaluate(wa_ws, """
    (() => {
        const buttons = Array.from(document.querySelectorAll('div[role="button"], button, a'));
        return buttons.map(b => ({
            tag: b.tagName,
            text: b.innerText.trim().slice(0,100),
            aria: b.getAttribute('aria-label') || '',
            href: b.getAttribute('href') || '',
            class: (b.className || '').slice(0,60)
        })).filter(b => b.text || b.aria || b.href).slice(0, 30);
    })()
    """)
    print(json.dumps(wa_page, indent=2))
    
    # Check for message input
    wa_input = await evaluate(wa_ws, """
    (() => {
        const inputs = Array.from(document.querySelectorAll('div[contenteditable="true"], input, textarea'));
        return inputs.map(i => ({
            tag: i.tagName,
            contenteditable: i.getAttribute('contenteditable') || '',
            dataTab: i.getAttribute('data-tab') || '',
            aria: i.getAttribute('aria-label') || '',
            placeholder: i.getAttribute('placeholder') || '',
            class: (i.className || '').slice(0,60),
            visible: i.offsetParent !== null
        })).filter(i => i.visible).slice(0, 20);
    })()
    """)
    print(f"Inputs: {json.dumps(wa_input, indent=2)}")
    
    # Check all visible text
    wa_text = await evaluate(wa_ws, """
    (() => {
        const divs = Array.from(document.querySelectorAll('div, span'));
        return divs.map(d => d.innerText.trim()).filter(t => t.length > 10 && t.length < 200).slice(0, 30);
    })()
    """)
    print(f"Text: {json.dumps(wa_text, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
