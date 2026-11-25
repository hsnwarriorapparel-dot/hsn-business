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
    print("\n=== INSTAGRAM: Send Button After Typing ===")
    ig_send_btn = await evaluate(ig_ws, """
    (() => {
        const all = Array.from(document.querySelectorAll('button, div[role="button"], svg'));
        return all.filter(el => {
            const aria = el.getAttribute('aria-label') || '';
            const title = el.getAttribute('title') || '';
            return aria.toLowerCase().includes('send') || 
                   title.toLowerCase().includes('send') ||
                   aria.toLowerCase().includes('paper') ||
                   title.toLowerCase().includes('paper');
        }).map(el => ({
            tag: el.tagName,
            aria: el.getAttribute('aria-label') || '',
            title: el.getAttribute('title') || '',
            class: (el.className || '').slice(0,60)
        }));
    })()
    """)
    print(json.dumps(ig_send_btn, indent=2))
    
    # Also check the voice clip button - it might change to send
    print("\n=== INSTAGRAM: Voice Clip / Send Area ===")
    ig_voice = await evaluate(ig_ws, """
    (() => {
        const all = Array.from(document.querySelectorAll('button, div[role="button"], svg'));
        return all.filter(el => {
            const aria = el.getAttribute('aria-label') || '';
            return aria.toLowerCase().includes('voice') || 
                   aria.toLowerCase().includes('clip') ||
                   aria.toLowerCase().includes('audio');
        }).map(el => ({
            tag: el.tagName,
            aria: el.getAttribute('aria-label') || '',
            title: el.getAttribute('title') || '',
            class: (el.className || '').slice(0,60),
            parent: el.parentElement ? (el.parentElement.className || '').slice(0,60) : ''
        }));
    })()
    """)
    print(json.dumps(ig_voice, indent=2))
    
    # Try clicking the voice clip area (might be send)
    ig_click_voice = await evaluate(ig_ws, """
    (() => {
        const all = Array.from(document.querySelectorAll('button, div[role="button"], svg'));
        const voiceBtn = all.find(el => {
            const aria = el.getAttribute('aria-label') || '';
            return aria.toLowerCase().includes('voice') || aria.toLowerCase().includes('clip');
        });
        if (voiceBtn) { voiceBtn.click(); return 'clicked_voice'; }
        return 'no_voice_button';
    })()
    """)
    print(f"Click voice: {ig_click_voice}")
    await asyncio.sleep(2)
    
    # Check thread for new message
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
