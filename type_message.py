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
    
    # Try using execCommand
    print("=== INSTAGRAM: Try execCommand ===")
    ig_exec = await evaluate(ig_ws, f"""
    (() => {{
        const inputs = Array.from(document.querySelectorAll('div[contenteditable="true"][role="textbox"]'));
        const inp = inputs.find(i => i.offsetParent !== null);
        if (inp) {{
            inp.focus();
            document.execCommand('selectAll', false, null);
            document.execCommand('delete', false, null);
            document.execCommand('insertText', false, `{dm_message.replace('`', '\\\\`').replace('${', '\\\\${')}`);
            return inp.innerText.slice(0, 100);
        }}
        return 'no_input';
    }})()
    """)
    print(f"execCommand: {ig_exec}")
    await asyncio.sleep(1)
    
    # Check input content
    ig_check_input = await evaluate(ig_ws, """
    (() => {
        const inputs = Array.from(document.querySelectorAll('div[contenteditable="true"][role="textbox"]'));
        const inp = inputs.find(i => i.offsetParent !== null);
        return inp ? inp.innerText.slice(0, 100) : 'no_input';
    })()
    """)
    print(f"Input content: {ig_check_input}")
    
    # Look for send button now
    ig_send = await evaluate(ig_ws, """
    (() => {
        const all = Array.from(document.querySelectorAll('svg, button, div[role="button"]'));
        return all.filter(el => {
            const aria = el.getAttribute('aria-label') || '';
            const title = el.getAttribute('title') || '';
            return aria.toLowerCase().includes('send') || 
                   title.toLowerCase().includes('send') ||
                   aria.toLowerCase().includes('paper');
        }).map(el => ({
            tag: el.tagName,
            aria: el.getAttribute('aria-label') || '',
            title: el.getAttribute('title') || '',
            class: (el.className || {}).baseVal ? (el.className.baseVal || '').slice(0,60) : ''
        }));
    })()
    """)
    print(f"Send button: {json.dumps(ig_send, indent=2)}")
    await asyncio.sleep(1)
    
    # Try Enter
    ig_enter = await evaluate(ig_ws, """
    (() => {
        const inputs = Array.from(document.querySelectorAll('div[contenteditable="true"][role="textbox"]'));
        const inp = inputs.find(i => i.offsetParent !== null);
        if (inp) {
            inp.focus();
            inp.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
            inp.dispatchEvent(new KeyboardEvent('keyup', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
            return 'enter';
        }
        return 'no_input';
    })()
    """)
    print(f"Enter: {ig_enter}")
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
