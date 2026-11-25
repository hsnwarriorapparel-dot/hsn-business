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
    
    # ============ INSTAGRAM: Click "Send message" (New message) ============
    print("=== INSTAGRAM: Click Send Message ===")
    ig_send_msg = await evaluate(ig_ws, """
    (() => {
        const buttons = Array.from(document.querySelectorAll('button, div[role="button"]'));
        const sendMsgBtn = buttons.find(b => b.innerText.trim() === 'Send message');
        if (sendMsgBtn) { sendMsgBtn.click(); return 'clicked_send_message'; }
        return 'not_found';
    })()
    """)
    print(f"Send message: {ig_send_msg}")
    await asyncio.sleep(2)
    
    # Search for shudokan.roje
    print("=== INSTAGRAM: Search User ===")
    ig_search = await evaluate(ig_ws, """
    (() => {
        const inputs = Array.from(document.querySelectorAll('input[type="text"], input[placeholder*="Search"], input[aria-label*="Search"]'));
        const searchInput = inputs.find(i => i.offsetParent !== null);
        if (searchInput) {
            searchInput.focus();
            searchInput.value = 'shudokan.roje';
            searchInput.dispatchEvent(new Event('input', {bubbles: true}));
            return 'typed_search';
        }
        return 'no_input';
    })()
    """)
    print(f"Search: {ig_search}")
    await asyncio.sleep(3)
    
    # Check search results
    print("=== INSTAGRAM: Search Results ===")
    ig_results = await evaluate(ig_ws, """
    (() => {
        const elements = Array.from(document.querySelectorAll('[role="option"], [role="button"], button, div[tabindex="0"], a, div.x1i10hfl'));
        return elements.map(e => ({
            text: e.innerText.trim().slice(0, 100),
            tag: e.tagName,
            class: e.className.slice(0, 50)
        })).filter(e => e.text.length > 0).slice(0, 20);
    })()
    """)
    print(json.dumps(ig_results, indent=2))
    
    # Click user result if found
    ig_click_user = await evaluate(ig_ws, """
    (() => {
        const elements = Array.from(document.querySelectorAll('[role="option"], [role="button"], button, div[tabindex="0"], a, div.x1i10hfl'));
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
    
    # Click Next
    ig_next = await evaluate(ig_ws, """
    (() => {
        const buttons = Array.from(document.querySelectorAll('button, div[role="button"]'));
        const nextBtn = buttons.find(b => {
            const text = b.innerText.toLowerCase().trim();
            return text === 'next' || text === 'chat';
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
            const buttons = Array.from(document.querySelectorAll('button, div[role="button"]'));
            const sendBtn = buttons.find(b => {{
                const text = b.innerText.toLowerCase().trim();
                const aria = b.getAttribute('aria-label')?.toLowerCase() || '';
                return text === 'send' || aria.includes('send');
            }});
            if (sendBtn) {{ sendBtn.click(); return 'sent'; }}
            return 'no_send_button';
        }}
        return 'no_textarea';
    }})()
    """)
    print(f"Send DM: {ig_send}")
    
    # ============ WHATSAPP: New Chat -> New Contact -> Add Number ============
    print("\n=== WHATSAPP: Click New Contact ===")
    wa_new_contact = await evaluate(wa_ws, """
    (() => {
        const elements = Array.from(document.querySelectorAll('[role="button"], button, div[tabindex], span[data-icon]'));
        const newContact = elements.find(e => {
            const text = e.innerText.trim();
            const icon = e.getAttribute('data-icon') || e.querySelector('[data-icon]')?.getAttribute('data-icon');
            return text === 'New contact' || icon === 'new-contact-filled';
        });
        if (newContact) { newContact.click(); return 'clicked_new_contact'; }
        return 'not_found';
    })()
    """)
    print(f"New contact: {wa_new_contact}")
    await asyncio.sleep(2)
    
    # Fill new contact form
    print("=== WHATSAPP: Fill Contact Form ===")
    wa_fill = await evaluate(wa_ws, """
    (() => {
        // Look for name and phone inputs
        const inputs = Array.from(document.querySelectorAll('input[type="text"], input[type="tel"], div[contenteditable="true"][role="textbox"]'));
        let filled = 0;
        for (const inp of inputs) {
            const placeholder = inp.getAttribute('placeholder') || '';
            const aria = inp.getAttribute('aria-label') || '';
            const label = inp.closest('label')?.innerText || '';
            const context = (placeholder + aria + label).toLowerCase();
            if (context.includes('name') && inp.offsetParent !== null) {
                inp.focus();
                inp.value = 'Shudokan Club';
                inp.dispatchEvent(new Event('input', {bubbles: true}));
                filled++;
            } else if ((context.includes('phone') || context.includes('mobile') || context.includes('number')) && inp.offsetParent !== null) {
                inp.focus();
                inp.value = '+34 661 571 463';
                inp.dispatchEvent(new Event('input', {bubbles: true}));
                filled++;
            }
        }
        return `filled_${filled}_fields`;
    })()
    """)
    print(f"Fill form: {wa_fill}")
    await asyncio.sleep(1)
    
    # Save contact
    wa_save = await evaluate(wa_ws, """
    (() => {
        const buttons = Array.from(document.querySelectorAll('button, div[role="button"]'));
        const saveBtn = buttons.find(b => {
            const text = b.innerText.toLowerCase().trim();
            const aria = b.getAttribute('aria-label')?.toLowerCase() || '';
            return text === 'save' || aria.includes('save');
        });
        if (saveBtn) { saveBtn.click(); return 'clicked_save'; }
        return 'no_save';
    })()
    """)
    print(f"Save: {wa_save}")
    await asyncio.sleep(2)
    
    # Now search and message
    print("=== WHATSAPP: Search Contact ===")
    wa_search = await evaluate(wa_ws, """
    (() => {
        const inputs = Array.from(document.querySelectorAll('div[contenteditable="true"][role="textbox"], div[contenteditable="true"][data-tab], input[type="text"]'));
        const searchInput = inputs.find(i => i.offsetParent !== null);
        if (searchInput) {
            searchInput.focus();
            searchInput.innerText = 'Shudokan';
            searchInput.dispatchEvent(new Event('input', {bubbles: true}));
            return 'typed_search';
        }
        return 'no_input';
    })()
    """)
    print(f"Search: {wa_search}")
    await asyncio.sleep(2)
    
    # Click chat
    wa_click = await evaluate(wa_ws, """
    (() => {
        const chats = Array.from(document.querySelectorAll('[role="listitem"], [role="button"][tabindex], div[tabindex="-1"]'));
        const target = chats.find(c => c.innerText.includes('Shudokan') || c.innerText.includes('661 571 463'));
        if (target) { target.click(); return 'clicked_chat'; }
        return 'chat_not_found';
    })()
    """)
    print(f"Click chat: {wa_click}")
    await asyncio.sleep(2)
    
    # Send message
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
