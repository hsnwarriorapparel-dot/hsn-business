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
    
    # ============ INSTAGRAM ============
    print("=== INSTAGRAM: Search shudokan.roje ===")
    # Type in search and press Enter
    ig_search = await evaluate(ig_ws, """
    (() => {
        const inputs = Array.from(document.querySelectorAll('input[placeholder="Search"], input[placeholder="Search..."]'));
        const searchInput = inputs.find(i => i.offsetParent !== null);
        if (searchInput) {
            searchInput.focus();
            searchInput.value = 'shudokan.roje';
            searchInput.dispatchEvent(new Event('input', {bubbles: true}));
            // Press Enter
            searchInput.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
            searchInput.dispatchEvent(new KeyboardEvent('keyup', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
            return 'typed_and_entered';
        }
        return 'no_input';
    })()
    """)
    print(f"Search: {ig_search}")
    await asyncio.sleep(4)
    
    # Check search results again
    print("=== INSTAGRAM: Search Results After Enter ===")
    ig_results = await evaluate(ig_ws, """
    (() => {
        const elements = Array.from(document.querySelectorAll('[role="option"], [role="button"], button, div[tabindex="0"], a, div.x1i10hfl.x1qjc9v5'));
        return elements.map(e => ({
            text: e.innerText.trim().slice(0, 100),
            tag: e.tagName,
            class: e.className.slice(0, 60)
        })).filter(e => e.text.length > 0).slice(0, 25);
    })()
    """)
    print(json.dumps(ig_results, indent=2))
    
    # Click shudokan result if found
    ig_click = await evaluate(ig_ws, """
    (() => {
        const elements = Array.from(document.querySelectorAll('[role="option"], [role="button"], button, div[tabindex="0"], a, div.x1i10hfl.x1qjc9v5'));
        const target = elements.find(e => {
            const text = e.innerText.toLowerCase();
            return text.includes('shudokan') || text.includes('roje');
        });
        if (target) { target.click(); return 'clicked_user'; }
        return 'user_not_found';
    })()
    """)
    print(f"Click user: {ig_click}")
    await asyncio.sleep(2)
    
    # Click "Chat" button
    ig_chat = await evaluate(ig_ws, """
    (() => {
        const buttons = Array.from(document.querySelectorAll('button, div[role="button"]'));
        const chatBtn = buttons.find(b => b.innerText.trim() === 'Chat');
        if (chatBtn) { chatBtn.click(); return 'clicked_chat'; }
        return 'no_chat_button';
    })()
    """)
    print(f"Click Chat: {ig_chat}")
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
    
    # ============ WHATSAPP ============
    print("\n=== WHATSAPP: Fill Contact Form & Save ===")
    # Fill first name
    wa_first = await evaluate(wa_ws, """
    (() => {
        const inputs = Array.from(document.querySelectorAll('div[aria-label="First name"][role="textbox"]'));
        const inp = inputs.find(i => i.offsetParent !== null);
        if (inp) { inp.focus(); inp.innerText = 'Shudokan'; inp.dispatchEvent(new Event('input', {bubbles: true})); return 'filled_first'; }
        return 'no_first';
    })()
    """)
    print(f"First name: {wa_first}")
    
    # Fill last name
    wa_last = await evaluate(wa_ws, """
    (() => {
        const inputs = Array.from(document.querySelectorAll('div[aria-label="Last name"][role="textbox"]'));
        const inp = inputs.find(i => i.offsetParent !== null);
        if (inp) { inp.focus(); inp.innerText = 'Club'; inp.dispatchEvent(new Event('input', {bubbles: true})); return 'filled_last'; }
        return 'no_last';
    })()
    """)
    print(f"Last name: {wa_last}")
    
    # Fill phone
    wa_phone = await evaluate(wa_ws, """
    (() => {
        const inputs = Array.from(document.querySelectorAll('input[aria-label="Phone number"]'));
        const inp = inputs.find(i => i.offsetParent !== null);
        if (inp) { inp.focus(); inp.value = '+34 661 571 463'; inp.dispatchEvent(new Event('input', {bubbles: true})); return 'filled_phone'; }
        return 'no_phone';
    })()
    """)
    print(f"Phone: {wa_phone}")
    await asyncio.sleep(1)
    
    # Click "Add contact" (save button)
    wa_save = await evaluate(wa_ws, """
    (() => {
        const buttons = Array.from(document.querySelectorAll('button, div[role="button"]'));
        const saveBtn = buttons.find(b => b.innerText.trim() === 'Add contact');
        if (saveBtn) { saveBtn.click(); return 'clicked_add_contact'; }
        return 'no_add_contact';
    })()
    """)
    print(f"Save: {wa_save}")
    await asyncio.sleep(3)
    
    # Search for contact
    print("=== WHATSAPP: Search Contact ===")
    wa_search = await evaluate(wa_ws, """
    (() => {
        const inputs = Array.from(document.querySelectorAll('div[aria-label="Search or start a new chat"][role="textbox"]'));
        const inp = inputs.find(i => i.offsetParent !== null);
        if (inp) { inp.focus(); inp.innerText = 'Shudokan'; inp.dispatchEvent(new Event('input', {bubbles: true})); return 'typed_search'; }
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
        const inputs = Array.from(document.querySelectorAll('div[contenteditable="true"][role="textbox"][data-tab="10"], div[contenteditable="true"][title="Type a message"], footer div[contenteditable="true"]'));
        const input = inputs.find(i => i.offsetParent !== null);
        if (input) {{
            input.focus();
            input.innerText = `{wa_message.replace('`', '\\\\`').replace('${', '\\\\${')}`;
            input.dispatchEvent(new Event('input', {{bubbles: true}}));
            const buttons = Array.from(document.querySelectorAll('button[aria-label="Send"], button[data-testid="compose-btn-send"], span[data-icon="send"]'));
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
