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
    
    # Wait a bit for message dialog to open
    await asyncio.sleep(2)
    
    # Check current state - should be in DM composer
    print("=== INSTAGRAM: After Message Click ===")
    ig_state = await evaluate(ig_ws, """
    (() => {
        const buttons = Array.from(document.querySelectorAll('button, div[role="button"]'));
        const inputs = Array.from(document.querySelectorAll('textarea, input, div[contenteditable="true"]'));
        return {
            buttons: buttons.map(b => ({text: b.innerText.trim().slice(0,50), aria: b.getAttribute('aria-label')||'', class: b.className.slice(0,40)})).filter(b => b.text),
            inputs: inputs.map(i => ({tag: i.tagName, placeholder: i.getAttribute('placeholder')||'', aria: i.getAttribute('aria-label')||'', role: i.getAttribute('role')||'', class: i.className.slice(0,40)})).filter(i => i.placeholder || i.aria || i.role)
        };
    })()
    """)
    print(json.dumps(ig_state, indent=2))
    
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

if __name__ == "__main__":
    asyncio.run(main())
