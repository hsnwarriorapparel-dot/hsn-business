import asyncio
import json
import websockets

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
    ig_ws = "ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC"
    wa_ws = "ws://127.0.0.1:9222/devtools/page/93073410C8FA7BC7FB363FD9EC35BD7E"
    
    # Enable Runtime
    for ws in [ig_ws, wa_ws]:
        await send_cdp(ws, "Runtime.enable")
    
    # ============ INSTAGRAM: Find and DM @shudokan.roje ============
    print("=== INSTAGRAM ===")
    
    # Search for shudokan.roje in DM list
    search_js = """
    (async () => {
        // Look for existing chat with shudokan.roje
        const threads = document.querySelectorAll('[role="listitem"], .x1lliihq, .x1iyjqo2');
        for (const t of threads) {
            const text = t.innerText.toLowerCase();
            if (text.includes('shudokan') || text.includes('roje')) {
                t.click();
                return 'found_existing';
            }
        }
        // Click new message button
        const newBtn = document.querySelector('svg[aria-label="New message"], button[aria-label="New message"], div[role="button"]:has(svg[aria-label="New message"])');
        if (newBtn) { newBtn.click(); return 'clicked_new'; }
        return 'no_new_btn';
    })()
    """
    result = await evaluate(ig_ws, search_js)
    print(f"Search result: {result}")
    await asyncio.sleep(2)
    
    # If new message, search for user
    search_user_js = """
    (async () => {
        await new Promise(r => setTimeout(r, 1000));
        const input = document.querySelector('input[placeholder*="Search"], input[aria-label*="Search"], input[type="text"]');
        if (input) {
            input.focus();
            input.value = 'shudokan.roje';
            input.dispatchEvent(new Event('input', {bubbles: true}));
            await new Promise(r => setTimeout(r, 2000));
            // Click the user result
            const results = document.querySelectorAll('[role="option"], .x1lliihq, .x1iyjqo2');
            for (const r of results) {
                if (r.innerText.toLowerCase().includes('shudokan') || r.innerText.toLowerCase().includes('roje')) {
                    r.click();
                    return 'clicked_user';
                }
            }
            return 'user_not_found';
        }
        return 'no_search_input';
    })()
    """
    result = await evaluate(ig_ws, search_user_js)
    print(f"Search user result: {result}")
    await asyncio.sleep(2)
    
    # Click Next/Chat button
    next_js = """
    (async () => {
        const btns = Array.from(document.querySelectorAll('button, div[role="button"]'));
        const nextBtn = btns.find(b => b.innerText.toLowerCase().includes('next') || b.innerText.toLowerCase().includes('chat'));
        if (nextBtn) { nextBtn.click(); return 'clicked_next'; }
        return 'no_next_btn';
    })()
    """
    result = await evaluate(ig_ws, next_js)
    print(f"Next button result: {result}")
    await asyncio.sleep(2)
    
    # Send DM message
    dm_message = """Hola! 👋

Soy HSN Warrior Apparels (Sialkot, Pakistán) — fabricantes B2B de uniformes y equipamiento para artes marciales desde 2011.

Vi que Club Deportivo ROJE SHUDOKAN (Güímar, Tenerife) practica Judo, Kickboxing y Ju-Jitsu. Perfecto ajuste para nuestro catálogo.

He preparado un "Starter Kit" a medida para vuestro club — 340 unidades cubriendo las 3 disciplinas, con vuestro logo gratis, envío puerta a puerta DDP Tenerife (aduanas incluidas, cero sorpresas), producción 4-6 semanas.

¿Os interesa que os envíe la propuesta formal por email (info@shudokan.es) o WhatsApp (+34 661 571 463)?

Quedo a vuestra disposición.
— HSN Warrior Apparels"""
    
    send_dm_js = f"""
    (async () => {{
        await new Promise(r => setTimeout(r, 1000));
        const textarea = document.querySelector('textarea[placeholder*="Message"], textarea[aria-label*="Message"], div[contenteditable="true"][role="textbox"]');
        if (textarea) {{
            textarea.focus();
            textarea.value = `{dm_message.replace('`', '\\`').replace('${', '\\${')}`;
            textarea.dispatchEvent(new Event('input', {{bubbles: true}}));
            await new Promise(r => setTimeout(r, 500));
            // Find send button
            const btns = Array.from(document.querySelectorAll('button, div[role="button"]'));
            const sendBtn = btns.find(b => b.innerText.toLowerCase().includes('send') || b.querySelector('svg[aria-label*="Send"]'));
            if (sendBtn) {{ sendBtn.click(); return 'sent'; }}
            return 'no_send_btn';
        }}
        return 'no_textarea';
    }})()
    """
    result = await evaluate(ig_ws, send_dm_js)
    print(f"Send DM result: {result}")
    
    # ============ WHATSAPP: Find and message +34 661 571 463 ============
    print("\n=== WHATSAPP ===")
    
    wa_search_js = """
    (async () => {
        // Search for contact
        const searchBox = document.querySelector('div[contenteditable="true"][data-tab="3"], div[title="Search input textbox"]');
        if (searchBox) {
            searchBox.focus();
            searchBox.innerText = '+34 661 571 463';
            searchBox.dispatchEvent(new Event('input', {bubbles: true}));
            await new Promise(r => setTimeout(r, 3000));
            // Click the chat
            const chats = document.querySelectorAll('[role="listitem"], ._ak8l, ._ak8o');
            for (const c of chats) {
                if (c.innerText.includes('661 571 463') || c.innerText.includes('661571463')) {
                    c.click();
                    return 'found_chat';
                }
            }
            return 'chat_not_found';
        }
        return 'no_search_box';
    })()
    """
    result = await evaluate(wa_ws, wa_search_js)
    print(f"WhatsApp search result: {result}")
    await asyncio.sleep(2)
    
    wa_message = """Hola! 👋

HSN Warrior Apparels aquí (fabricantes B2B artes marciales, Sialkot, Pakistán desde 2011).

Seguimiento a vuestra consulta sobre catálogo y precios para kickboxing/uniformes. He preparado propuesta a medida "Starter Kit" 340 uds (Judo/Kickboxing/Ju-Jitsu), logo gratis, envío DDP Tenerife (aduanas incluidas), 4-6 sem producción.

¿Os envío la propuesta formal por email (info@shudokan.es) o seguimos por aquí?

Quedo a vuestra disposición.
— HSN Warrior Apparels"""
    
    wa_send_js = f"""
    (async () => {{
        await new Promise(r => setTimeout(r, 1000));
        const input = document.querySelector('div[contenteditable="true"][data-tab="10"], div[title="Type a message"], footer div[contenteditable="true"]');
        if (input) {{
            input.focus();
            input.innerText = `{wa_message.replace('`', '\\`').replace('${', '\\${')}`;
            input.dispatchEvent(new Event('input', {{bubbles: true}}));
            await new Promise(r => setTimeout(r, 500));
            // Send button
            const sendBtn = document.querySelector('button[aria-label="Send"], button[data-testid="compose-btn-send"], span[data-icon="send"]');
            if (sendBtn) {{ sendBtn.click(); return 'sent'; }}
            return 'no_send_btn';
        }}
        return 'no_input';
    }})()
    """
    result = await evaluate(wa_ws, wa_send_js)
    print(f"WhatsApp send result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
