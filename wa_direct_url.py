import asyncio
import json
import websockets
import aiohttp
import urllib.parse

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
    
    # Read WhatsApp message
    with open('/home/ubuntu/shudokan_wa_v2.txt', 'r') as f:
        wa_message = f.read()
    
    # Navigate to direct chat URL
    encoded_msg = urllib.parse.quote(wa_message)
    direct_url = f"https://web.whatsapp.com/send?phone=34661571463&text={encoded_msg}"
    print(f"Direct URL: {direct_url}")
    
    wa_nav = await evaluate(wa_ws, f"""
    (() => {{
        window.location.href = '{direct_url}';
        return 'navigated';
    }})()
    """)
    print(f"Navigate: {wa_nav}")
    await asyncio.sleep(8)
    
    # Re-get WS after navigation
    wa_ws = await get_wa_ws()
    if not wa_ws:
        print("WhatsApp tab lost")
        return
    
    print(f"New WhatsApp WS: {wa_ws}")
    await send_cdp(wa_ws, "Runtime.enable")
    
    # Check page
    wa_info = await evaluate(wa_ws, """
    (() => ({
        title: document.title,
        url: window.location.href
    }))()
    """)
    print(f"Page: {json.dumps(wa_info, indent=2)}")
    
    # Wait for chat to load and send (might need to click "Continue to Chat" or similar)
    wa_continue = await evaluate(wa_ws, """
    (() => {
        const buttons = Array.from(document.querySelectorAll('div[role="button"], button, a'));
        const cont = buttons.find(b => {
            const text = b.innerText.toLowerCase();
            const aria = b.getAttribute('aria-label') || '';
            return text.includes('continue') || text.includes('chat') || aria.includes('continue') || aria.includes('chat');
        });
        if (cont) { cont.click(); return 'clicked_continue'; }
        return 'no_continue';
    })()
    """)
    print(f"Continue: {wa_continue}")
    await asyncio.sleep(3)
    
    # Send message (might already be filled from URL)
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
    await asyncio.sleep(2)
    
    # Verify
    wa_verify = await evaluate(wa_ws, """
    (() => {
        const msgs = Array.from(document.querySelectorAll('span[dir="ltr"], div[data-testid="msg-container"]'));
        return msgs.map(m => m.innerText.trim()).filter(t => t.includes('Starter Kit') || t.includes('DDP Tenerife')).slice(0, 5);
    })()
    """)
    print(f"Verify: {json.dumps(wa_verify, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
