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
    
    # Press Enter in the message input (message should be pre-filled from URL)
    print("=== WHATSAPP: Send Pre-filled Message ===")
    wa_send = await evaluate(wa_ws, """
    (() => {
        const msgBox = document.querySelector('div[contenteditable="true"][data-tab="10"]');
        if (msgBox) {
            msgBox.focus();
            msgBox.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
            msgBox.dispatchEvent(new KeyboardEvent('keyup', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
            return 'sent_enter';
        }
        return 'no_msg_box';
    })()
    """)
    print(f"Send: {wa_send}")
    await asyncio.sleep(3)
    
    # Verify
    wa_verify = await evaluate(wa_ws, """
    (() => {
        const msgs = Array.from(document.querySelectorAll('span[dir="ltr"], div[data-testid="msg-container"], div.message-out'));
        return msgs.map(m => m.innerText.trim()).filter(t => t.includes('Starter Kit') || t.includes('DDP Tenerife') || t.includes('kit espec')).slice(0, 5);
    })()
    """)
    print(f"Verify: {json.dumps(wa_verify, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
