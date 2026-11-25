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
    
    # Fill message
    dm_message = """Hola! 👋

Soy HSN Warrior Apparels (Sialkot, Pakistán) — fabricantes B2B de uniformes y equipamiento para artes marciales desde 2011.

Vi que Club Deportivo ROJE SHUDOKAN (Güímar, Tenerife) practica Judo, Kickboxing y Ju-Jitsu. Perfecto ajuste para nuestro catálogo.

He preparado un "Starter Kit" a medida para vuestro club — 340 unidades cubriendo las 3 disciplinas, con vuestro logo gratis, envío puerta a puerta DDP Tenerife (aduanas incluidas, cero sorpresas), producción 4-6 semanas.

¿Os interesa que os envíe la propuesta formal por email (info@shudokan.es) o WhatsApp (+34 661 571 463)?

Quedo a vuestra disposición.
— HSN Warrior Apparels"""
    
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
    
    # Find the Voice Clip SVG's parent clickable element
    print("\n=== INSTAGRAM: Find Voice Clip Parent ===")
    ig_voice_parent = await evaluate(ig_ws, """
    (() => {
        const svgs = Array.from(document.querySelectorAll('svg[aria-label="Voice Clip"]'));
        const svg = svgs[0];
        if (!svg) return 'no_voice_svg';
        
        // Walk up to find clickable parent
        let el = svg.parentElement;
        while (el && el.tagName !== 'BODY') {
            const role = el.getAttribute('role');
            const tag = el.tagName;
            const className = el.className || '';
            if (tag === 'BUTTON' || tag === 'A' || role === 'button' || className.includes('x1i10hfl')) {
                return {
                    tag: el.tagName,
                    role: el.getAttribute('role') || '',
                    class: className.slice(0,80),
                    clickable: true
                };
            }
            el = el.parentElement;
        }
        return 'no_clickable_parent';
    })()
    """)
    print(json.dumps(ig_voice_parent, indent=2))
    
    # Try clicking the voice clip parent button
    ig_click_parent = await evaluate(ig_ws, """
    (() => {
        const svgs = Array.from(document.querySelectorAll('svg[aria-label="Voice Clip"]'));
        const svg = svgs[0];
        if (!svg) return 'no_voice_svg';
        
        let el = svg.parentElement;
        while (el && el.tagName !== 'BODY') {
            const role = el.getAttribute('role');
            const tag = el.tagName;
            const className = el.className || '';
            if (tag === 'BUTTON' || tag === 'A' || role === 'button' || className.includes('x1i10hfl')) {
                el.click();
                return 'clicked_parent';
            }
            el = el.parentElement;
        }
        return 'no_clickable_parent';
    })()
    """)
    print(f"Click parent: {ig_click_parent}")
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
