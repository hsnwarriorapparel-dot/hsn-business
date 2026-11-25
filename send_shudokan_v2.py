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
    
    for ws in [ig_ws, wa_ws]:
        await send_cdp(ws, "Runtime.enable")
    
    # ============ INSTAGRAM: Click "New message" ============
    print("=== INSTAGRAM: Click New Message ===")
    ig_click_new = await evaluate(ig_ws, """
    (() => {
        // Find "New message" button by text content
        const buttons = Array.from(document.querySelectorAll('button, div[role="button"], a[role="button"]'));
        const newMsgBtn = buttons.find(b => b.innerText.trim() === 'New message' || b.innerText.includes('New message'));
        if (newMsgBtn) { newMsgBtn.click(); return 'clicked_new_message'; }
        // Try by aria-label
        const byAria = document.querySelector('[aria-label="New message"], [aria-label*="New message"]');
        if (byAria) { byAria.click(); return 'clicked_by_aria'; }
        return 'not_found';
    })()
    """)
    print(f"Click new message: {ig_click_new}")
    await asyncio.sleep(2)
    
    # Search for shudokan.roje
    print("=== INSTAGRAM: Search User ===")
    ig_search = await evaluate(ig_ws, """
    (() => {
        const inputs = Array.from(document.querySelectorAll('input[type="text"], input[placeholder*="Search"], input[aria-label*="Search"]'));
        const searchInput = inputs.find(i => i.offsetParent !== null); // visible
        if (searchInput) {
            searchInput.focus();
            searchInput.value = 'shudokan.roje';
            searchInput.dispatchEvent(new Event('input', {bubbles: true}));
            return 'typed_search';
        }
        // Try contenteditable
        const editable = document.querySelector('div[contenteditable="true"][role="textbox"], div[contenteditable="true"][data-focusable="true"]');
        if (editable) {
            editable.focus();
            editable.innerText = 'shudokan.roje';
            editable.dispatchEvent(new Event('input', {bubbles: true}));
            return 'typed_editable';
        }
        return 'no_input';
    })()
    """)
    print(f"Search: {ig_search}")
    await asyncio.sleep(3)
    
    # Click the user result
    print("=== INSTAGRAM: Click User Result ===")
    ig_click_user = await evaluate(ig_ws, """
    (() => {
        // Look for clickable elements containing shudokan/roje
        const elements = Array.from(document.querySelectorAll('[role="option"], [role="button"], button, div[tabindex="0"], a'));
        const target = elements.find(e => {
            const text = e.innerText.toLowerCase();
            return text.includes('shudokan') || text.includes('roje');
        });
        if (target) { target.click(); return 'clicked_user'; }
        return 'user_not_found';
    })()
    """)
    print(f"Click user: {ig_click_user}")
    await asyncio.sleep(2)
    
    # Click "Next" or "Chat" button
    print("=== INSTAGRAM: Click Next ===")
    ig_next = await evaluate(ig_ws, """
    (() => {
        const buttons = Array.from(document.querySelectorAll('button, div[role="button"]'));
        const nextBtn = buttons.find(b => {
            const text = b.innerText.toLowerCase();
            return text === 'next' || text === 'chat' || text.includes('next') || text.includes('chat');
        });
        if (nextBtn) { nextBtn.click(); return 'clicked_next'; }
        return 'no_next';
    })()
    """)
    print(f"Next: {ig_next}")
    await asyncio.sleep(2)
    
    # Send DM
    dm_message = """Hola! 👋

Soy HSN Warrior Apparels (Sialkot, Pakistán) — fabricantes B2B de uniformes y equipamiento para artes marciales desde 2011.

Vi que Club Deportivo ROJE SHUDOKAN (Güímar, Tenerife) practica Judo, Kickboxing y Ju-Jitsu. Perfecto ajuste para nuestro catálogo.

He preparado un "Starter Kit" a medida para vuestro club — 340 unidades cubriendo las 3 disciplinas, con vuestro logo gratis, envío puerta a puerta DDP Tenerife (aduanas incluidas, cero sorpresas), producción 4-6 semanas.

¿Os interesa que os envíe la propuesta formal por email (info@shudokan.es) o WhatsApp (+34 661 571 463)?

Quedo a vuestra disposición.
— HSN Warrior Apparels"""
    
    print("=== INSTAGRAM: Send DM ===")
    ig_send = await evaluate(ig_ws, f"""
    (() => {{
        const textareas = Array.from(document.querySelectorAll('textarea[placeholder*="Message"], textarea[aria-label*="Message"], div[contenteditable="true"][role="textbox"], div[contenteditable="true"][data-lexical-editor="true"]'));
        const ta = textareas.find(t => t.offsetParent !== null);
        if (ta) {{
            ta.focus();
            if (ta.tagName === 'TEXTAREA') {{
                ta.value = `{dm_message.replace('`', '\\\\`').replace('${', '\\\\${')}`;
                ta.dispatchEvent(new Event('input', {{bubbles: true}}));
            }} else {{
                ta.innerText = `{dm_message.replace('`', '\\\\`').replace('${', '\\\\${')}`;
                ta.dispatchEvent(new Event('input', {{bubbles: true}}));
            }}
            // Find send button
            const buttons = Array.from(document.querySelectorAll('button, div[role="button"]'));
            const sendBtn = buttons.find(b => {{
                const text = b.innerText.toLowerCase();
                const svg = b.querySelector('svg');
                const aria = b.getAttribute('aria-label')?.toLowerCase() || '';
                return text === 'send' || aria.includes('send') || (svg && svg.getAttribute('aria-label')?.toLowerCase().includes('send'));
            }});
            if (sendBtn) {{ sendBtn.click(); return 'sent'; }}
            return 'no_send_button';
        }}
        return 'no_textarea';
    }})()
    """)
    print(f"Send DM: {ig_send}")
    
    # ============ WHATSAPP: Click New Chat ============
    print("\n=== WHATSAPP: Click New Chat ===")
    wa_new_chat = await evaluate(wa_ws, """
    (() => {
        // Find new chat button by icon or aria-label
        const buttons = Array.from(document.querySelectorAll('button, div[role="button"], span[data-icon]'));
        const newChatBtn = buttons.find(b => {
            const icon = b.getAttribute('data-icon') || b.querySelector('[data-icon]')?.getAttribute('data-icon');
            const aria = b.getAttribute('aria-label') || '';
            return icon === 'new-chat-filled' || aria.includes('New chat') || aria.includes('new chat');
        });
        if (newChatBtn) { newChatBtn.click(); return 'clicked_new_chat'; }
        // Try by text
        const byText = buttons.find(b => b.innerText.trim() === 'New chat' || b.innerText.includes('New chat'));
        if (byText) { byText.click(); return 'clicked_by_text'; }
        return 'not_found';
    })()
    """)
    print(f"New chat: {wa_new_chat}")
    await asyncio.sleep(2)
    
    # Search for phone number
    print("=== WHATSAPP: Search Phone ===")
    wa_search = await evaluate(wa_ws, """
    (() => {
        const inputs = Array.from(document.querySelectorAll('div[contenteditable="true"][role="textbox"], div[contenteditable="true"][data-tab], input[type="text"]'));
        const searchInput = inputs.find(i => i.offsetParent !== null);
        if (searchInput) {
            searchInput.focus();
            searchInput.innerText = '+34 661 571 463';
            searchInput.dispatchEvent(new Event('input', {bubbles: true}));
            return 'typed_search';
        }
        return 'no_input';
    })()
    """)
    print(f"Search: {wa_search}")
    await asyncio.sleep(3)
    
    # Click the chat result
    print("=== WHATSAPP: Click Chat ===")
    wa_click_chat = await evaluate(wa_ws, """
    (() => {
        const chats = Array.from(document.querySelectorAll('[role="listitem"], [role="button"][tabindex], ._ak8l, ._ak8o, div[tabindex="-1"]'));
        const target = chats.find(c => c.innerText.includes('661 571 463') || c.innerText.includes('661571463'));
        if (target) { target.click(); return 'clicked_chat'; }
        return 'chat_not_found';
    })()
    """)
    print(f"Click chat: {wa_click_chat}")
    await asyncio.sleep(2)
    
    # Send WhatsApp message
    wa_message = """Hola! 👋

HSN Warrior Apparels aquí (fabricantes B2B artes marciales, Sialkot, Pakistán desde 2011).

Seguimiento a vuestra consulta sobre catálogo y precios para kickboxing/uniformes. He preparado propuesta a medida "Starter Kit" 340 uds (Judo/Kickboxing/Ju-Jitsu), logo gratis, envío DDP Tenerife (aduanas incluidas), 4-6 sem producción.

¿Os envío la propuesta formal por email (info@shudokan.es) o seguimos por aquí?

Quedo a vuestra disposición.
— HSN Warrior Apparels"""
    
    print("=== WHATSAPP: Send Message ===")
    wa_send = await evaluate(wa_ws, f"""
    (() => {{
        const inputs = Array.from(document.querySelectorAll('div[contenteditable="true"][role="textbox"][data-tab="10"], div[contenteditable="true"][title="Type a message"], footer div[contenteditable="true"], div[contenteditable="true"][aria-label*="Type"]'));
        const input = inputs.find(i => i.offsetParent !== null);
        if (input) {{
            input.focus();
            input.innerText = `{wa_message.replace('`', '\\\\`').replace('${', '\\\\${')}`;
            input.dispatchEvent(new Event('input', {{bubbles: true}}));
            // Send button
            const buttons = Array.from(document.querySelectorAll('button[aria-label="Send"], button[data-testid="compose-btn-send"], span[data-icon="send"], button:has(span[data-icon="send"])'));
            const sendBtn = buttons.find(b => b.offsetParent !== null);
            if (sendBtn) {{ sendBtn.click(); return 'sent'; }}
            return 'no_send_button';
        }}
        return 'no_input';
    }})()
    """)
    print(f"Send WhatsApp: {wa_send}")

if __name__ == "__main__":
    asyncio.run(main())
