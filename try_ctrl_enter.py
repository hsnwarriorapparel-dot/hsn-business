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
    
    dm_message = """Hola! 👋

Soy HSN Warrior Apparels (Sialkot, Pakistán) — fabricantes B2B de uniformes y equipamiento para artes marciales desde 2011.

Vi que Club Deportivo ROJE SHUDOKAN (Güímar, Tenerife) practica Judo, Kickboxing y Ju-Jitsu. Perfecto ajuste para nuestro catálogo.

He preparado un "Starter Kit" a medida para vuestro club — 340 unidades cubriendo las 3 disciplinas, con vuestro logo gratis, envío puerta a puerta DDP Tenerife (aduanas incluidas, cero sorpresas), producción 4-6 semanas.

¿Os interesa que os envíe la propuesta formal por email (info@shudokan.es) o WhatsApp (+34 661 571 463)?

Quedo a vuestra disposición.
— HSN Warrior Apparels"""
    
    # Fill message
    print("=== INSTAGRAM: Fill Message ===")
    ig_fill = await evaluate(ig_ws, f"""
    (() => {{
        const inputs = Array.from(document.querySelectorAll('div[contenteditable="true"][role="textbox"]'));
        const inp = inputs.find(i => i.offsetParent !== null);
        if (inp) {{
            inp.focus();
            inp.innerText = `{dm_message.replace('`', '\\\\`').replace('${', '\\\\${')}`;
            inp.dispatchEvent(new Event('input', {{bubbles: true}}));
            return 'filled';
        }}
        return 'no_input';
    }})()
    """)
    print(f"Fill: {ig_fill}")
    await asyncio.sleep(1)
    
    # Check for send button after typing
    print("\n=== INSTAGRAM: Check Send Button After Typing ===")
    send_after = await evaluate(ig_ws, """
    (() => {
        const all = Array.from(document.querySelectorAll('*'));
        return all.filter(el => {
            const aria = el.getAttribute('aria-label') || '';
            const testid = el.getAttribute('data-testid') || '';
            const title = el.getAttribute('title') || '';
            const text = el.innerText || '';
            return aria.toLowerCase().includes('send') || 
                   testid.toLowerCase().includes('send') ||
                   title.toLowerCase().includes('send') ||
                   (text.toLowerCase().trim() === 'send');
        }).map(el => ({
            tag: el.tagName,
            text: el.innerText?.trim().slice(0,50) || '',
            aria: el.getAttribute('aria-label') || '',
            testid: el.getAttribute('data-testid') || '',
            title: el.getAttribute('title') || '',
            class: el.className?.slice(0,60) || ''
        })).slice(0, 20);
    })()
    """)
    print(json.dumps(send_after, indent=2))
    
    # Try Ctrl+Enter
    print("\n=== INSTAGRAM: Try Ctrl+Enter ===")
    ig_ctrl = await evaluate(ig_ws, """
    (() => {
        const inputs = Array.from(document.querySelectorAll('div[contenteditable="true"][role="textbox"]'));
        const inp = inputs.find(i => i.offsetParent !== null);
        if (inp) {
            inp.focus();
            inp.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, ctrlKey: true, bubbles: true}));
            inp.dispatchEvent(new KeyboardEvent('keyup', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, ctrlKey: true, bubbles: true}));
            return 'ctrl_enter';
        }
        return 'no_input';
    })()
    """)
    print(f"Ctrl+Enter: {ig_ctrl}")
    await asyncio.sleep(2)
    
    # Check thread
    ig_check = await evaluate(ig_ws, """
    (() => {
        const allDivs = Array.from(document.querySelectorAll('div'));
        const messages = allDivs.map(d => d.innerText.trim()).filter(t => 
            t.includes('HSN Warrior') || t.includes('Starter Kit') || t.includes('DDP Tenerife')
        ).slice(0, 5);
        return messages;
    })()
    """)
    print(f"Thread check: {json.dumps(ig_check, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
