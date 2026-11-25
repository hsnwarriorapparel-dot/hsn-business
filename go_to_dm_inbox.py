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
    
    await send_cdp(ig_ws, "Runtime.enable")
    
    # Navigate to DM inbox
    print("=== INSTAGRAM: Go to DM Inbox ===")
    ig_nav = await evaluate(ig_ws, """
    (() => {
        window.location.href = 'https://instagram.com/direct/inbox/';
        return 'navigated';
    })()
    """)
    print(f"Navigate: {ig_nav}")
    await asyncio.sleep(4)
    
    # Check inbox state
    ig_inbox = await evaluate(ig_ws, """
    (() => {
        const allDivs = Array.from(document.querySelectorAll('div'));
        return allDivs.map(d => d.innerText.trim()).filter(t => 
            t.length > 5 && t.length < 200 && 
            (t.includes('shudokan') || t.includes('Shudokan') || t.includes('ROJE') || t.includes('Message') || t.includes('New') || t.includes('Send'))
        ).slice(0, 30);
    })()
    """)
    print(f"Inbox: {json.dumps(ig_inbox, indent=2)}")
    
    # Look for New Message / Send Message button
    ig_new = await evaluate(ig_ws, """
    (() => {
        const buttons = Array.from(document.querySelectorAll('button, div[role="button"], a[role="button"]'));
        const newBtn = buttons.find(b => {
            const text = b.innerText.toLowerCase().trim();
            const aria = b.getAttribute('aria-label')?.toLowerCase() || '';
            return text.includes('new') || text.includes('send message') || text.includes('write') || 
                   aria.includes('new') || aria.includes('send') || aria.includes('write');
        });
        if (newBtn) { newBtn.click(); return 'clicked_new'; }
        return 'no_new_button';
    })()
    """)
    print(f"New message: {ig_new}")
    await asyncio.sleep(2)
    
    # Search for shudokan
    ig_search = await evaluate(ig_ws, """
    (() => {
        const inputs = Array.from(document.querySelectorAll('input[placeholder*="Search"], input[aria-label*="Search"], div[contenteditable="true"][role="textbox"]'));
        const inp = inputs.find(i => i.offsetParent !== null);
        if (inp) {
            inp.focus();
            inp.value = 'shudokan.roje';
            inp.innerText = 'shudokan.roje';
            inp.dispatchEvent(new Event('input', {bubbles: true}));
            inp.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
            return 'searched';
        }
        return 'no_input';
    })()
    """)
    print(f"Search: {ig_search}")
    await asyncio.sleep(3)
    
    # Click result
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
    
    # Click Next/Chat
    ig_next = await evaluate(ig_ws, """
    (() => {
        const buttons = Array.from(document.querySelectorAll('button, div[role="button"]'));
        const nextBtn = buttons.find(b => {
            const text = b.innerText.toLowerCase().trim();
            return text === 'next' || text === 'chat' || text === 'continue';
        });
        if (nextBtn) { nextBtn.click(); return 'clicked_next'; }
        return 'no_next';
    })()
    """)
    print(f"Next/Chat: {ig_next}")
    await asyncio.sleep(2)
    
    # Send message
    dm_message = """Hola! 👋

Soy HSN Warrior Apparels (Sialkot, Pakistán) — fabricantes B2B de uniformes y equipamiento para artes marciales desde 2011.

Vi que Club Deportivo ROJE SHUDOKAN (Güímar, Tenerife) practica Judo, Kickboxing y Ju-Jitsu. Perfecto ajuste para nuestro catálogo.

He preparado un "Starter Kit" a medida para vuestro club — 340 unidades cubriendo las 3 disciplinas, con vuestro logo gratis, envío puerta a puerta DDP Tenerife (aduanas incluidas, cero sorpresas), producción 4-6 semanas.

¿Os interesa que os envíe la propuesta formal por email (info@shudokan.es) o WhatsApp (+34 661 571 463)?

Quedo a vuestra disposición.
— HSN Warrior Apparels"""
    
    ig_send = await evaluate(ig_ws, f"""
    (() => {{
        const inputs = Array.from(document.querySelectorAll('textarea[placeholder*="Message"], div[contenteditable="true"][role="textbox"], div[contenteditable="true"][data-lexical-editor="true"]'));
        const inp = inputs.find(i => i.offsetParent !== null);
        if (inp) {{
            inp.focus();
            if (inp.tagName === 'TEXTAREA') {{
                inp.value = `{dm_message.replace('`', '\\\\`').replace('${', '\\\\${')}`;
            }} else {{
                inp.innerText = `{dm_message.replace('`', '\\\\`').replace('${', '\\\\${')}`;
            }}
            inp.dispatchEvent(new Event('input', {{bubbles: true}}));
            // Try Enter
            inp.dispatchEvent(new KeyboardEvent('keydown', {{key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}}));
            inp.dispatchEvent(new KeyboardEvent('keyup', {{key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}}));
            return 'sent_enter';
        }}
        return 'no_input';
    }})()
    """)
    print(f"Send: {ig_send}")
    await asyncio.sleep(2)
    
    # Check thread
    ig_check = await evaluate(ig_ws, """
    (() => {
        const allDivs = Array.from(document.querySelectorAll('div'));
        const messages = allDivs.map(d => d.innerText.trim()).filter(t => 
            t.includes('Starter Kit') || t.includes('DDP Tenerife') || t.includes('340 unidades')
        ).slice(0, 5);
        return messages;
    })()
    """)
    print(f"Thread check: {json.dumps(ig_check, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
