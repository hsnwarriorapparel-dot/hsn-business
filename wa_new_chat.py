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
    
    # Read WhatsApp message
    with open('/home/ubuntu/shudokan_wa_v2.txt', 'r') as f:
        wa_message = f.read()
    
    # Click "New chat" button
    print("=== WHATSAPP: Click New Chat ===")
    wa_newchat = await evaluate(wa_ws, """
    (() => {
        const buttons = Array.from(document.querySelectorAll('div[role="button"], button'));
        const newChat = buttons.find(b => {
            const aria = b.getAttribute('aria-label') || '';
            return aria === 'New chat' || aria.includes('New chat');
        });
        if (newChat) { newChat.click(); return 'clicked_new_chat'; }
        return 'no_new_chat';
    })()
    """)
    print(f"New chat: {wa_newchat}")
    await asyncio.sleep(2)
    
    # Search for the number in the new chat search
    print("\n=== WHATSAPP: Search in New Chat ===")
    wa_search2 = await evaluate(wa_ws, """
    (() => {
        const searchBox = document.querySelector('input[aria-label="Search or start a new chat"], input[placeholder="Search or start a new chat"]');
        if (searchBox) {
            searchBox.focus();
            searchBox.value = '+34 661 571 463';
            searchBox.dispatchEvent(new Event('input', {bubbles: true}));
            searchBox.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
            return 'searched';
        }
        return 'no_search_box';
    })()
    """)
    print(f"Search: {wa_search2}")
    await asyncio.sleep(3)
    
    # Check results
    wa_results = await evaluate(wa_ws, """
    (() => {
        const items = Array.from(document.querySelectorAll('div[role="row"], div[role="listitem"], div._ak8l, div[tabindex="-1"]'));
        return items.map(i => ({
            text: i.innerText.trim().slice(0,150),
            class: (i.className || '').slice(0,80)
        })).filter(i => i.text.length > 0).slice(0, 20);
    })()
    """)
    print(f"Results: {json.dumps(wa_results, indent=2)}")
    
    # Click the result (should be the phone number)
    wa_click = await evaluate(wa_ws, """
    (() => {
        const items = Array.from(document.querySelectorAll('div[role="row"], div[role="listitem"], div._ak8l, div[tabindex="-1"]'));
        const target = items.find(i => i.innerText.includes('661') || i.innerText.includes('34'));
        if (target) { target.click(); return 'clicked_result'; }
        return 'no_result';
    })()
    """)
    print(f"Click result: {wa_click}")
    await asyncio.sleep(2)
    
    # Send message
    print("\n=== WHATSAPP: Send Message ===")
    wa_send = await evaluate(wa_ws, f"""
    (() => {{
        const msgBox = document.querySelector('div[contenteditable="true"][data-tab="10"]');
        if (msgBox) {{
            msgBox.focus();
            msgBox.innerText = `{wa_message.replace('`', '\\\\`').replace('${', '\\\\${')}`;
            msgBox.dispatchEvent(new Event('input', {{bubbles: true}}));
            msgBox.dispatchEvent(new KeyboardEvent('keydown', {{key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}}));
            msgBox.dispatchEvent(new KeyboardEvent('keyup', {{key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}}));
            return 'sent';
        }}
        return 'no_msg_box';
    }})()
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
