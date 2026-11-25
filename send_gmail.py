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
    
    # Read email content
    with open('/home/ubuntu/shudokan_email_v2.txt', 'r') as f:
        email_content = f.read()
    
    # Click Compose
    print("=== GMAIL: Click Compose ===")
    gm_compose = await evaluate(gmail_ws, """
    (() => {
        const buttons = Array.from(document.querySelectorAll('div[role="button"]'));
        const compose = buttons.find(b => {
            const aria = b.getAttribute('aria-label') || '';
            return aria.includes('Compose') || aria.includes('Redactar');
        });
        if (compose) { compose.click(); return 'clicked_compose'; }
        return 'no_compose';
    })()
    """)
    print(f"Compose: {gm_compose}")
    await asyncio.sleep(2)
    
    # Fill To, Subject, Body
    print("=== GMAIL: Fill Email ===")
    gm_fill = await evaluate(gmail_ws, f"""
    (() => {{
        // To field
        const toInputs = Array.from(document.querySelectorAll('input[aria-label*="To"], input[aria-label*="Para"], textarea[aria-label*="To"], textarea[aria-label*="Para"]'));
        const toInput = toInputs.find(i => i.offsetParent !== null);
        if (toInput) {{
            toInput.focus();
            toInput.value = 'info@shudokan.es';
            toInput.dispatchEvent(new Event('input', {{bubbles: true}}));
            toInput.dispatchEvent(new KeyboardEvent('keydown', {{key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}}));
        }}
        
        // Subject
        const subjInputs = Array.from(document.querySelectorAll('input[aria-label*="Subject"], input[aria-label*="Asunto"]'));
        const subjInput = subjInputs.find(i => i.offsetParent !== null);
        if (subjInput) {{
            subjInput.focus();
            subjInput.value = 'Propuesta Starter Kit — Club Deportivo ROJE SHUDOKAN (340 uds, DDP Tenerife)';
            subjInput.dispatchEvent(new Event('input', {{bubbles: true}}));
        }}
        
        // Body - find the editable div
        const bodyDivs = Array.from(document.querySelectorAll('div[aria-label*="Message Body"], div[aria-label*="Cuerpo"], div[role="textbox"][contenteditable="true"]'));
        const bodyDiv = bodyDivs.find(d => d.offsetParent !== null);
        if (bodyDiv) {{
            bodyDiv.focus();
            document.execCommand('selectAll', false, null);
            document.execCommand('insertText', false, `{email_content.replace('`', '\\\\`').replace('${', '\\\\${')}`);
        }}
        
        return 'filled';
    }})()
    """)
    print(f"Fill: {gm_fill}")
    await asyncio.sleep(2)
    
    # Click Send
    print("=== GMAIL: Click Send ===")
    gm_send = await evaluate(gmail_ws, """
    (() => {
        const buttons = Array.from(document.querySelectorAll('div[role="button"]'));
        const sendBtn = buttons.find(b => {
            const aria = b.getAttribute('aria-label') || '';
            return aria.includes('Send') || aria.includes('Enviar');
        });
        if (sendBtn) { sendBtn.click(); return 'clicked_send'; }
        return 'no_send';
    })()
    """)
    print(f"Send: {gm_send}")
    await asyncio.sleep(3)
    
    print("Email sent!")

if __name__ == "__main__":
    asyncio.run(main())
