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
    
    # ============ INSTAGRAM: Navigate directly to profile ============
    print("=== INSTAGRAM: Navigate to @shudokan.roje ===")
    ig_nav = await evaluate(ig_ws, """
    (() => {
        window.location.href = 'https://instagram.com/shudokan.roje';
        return 'navigated';
    })()
    """)
    print(f"Navigate: {ig_nav}")
    await asyncio.sleep(5)
    
    # Check if profile exists
    ig_profile = await evaluate(ig_ws, """
    (() => {
        const texts = Array.from(document.querySelectorAll('h1, h2, header, section, main'));
        return texts.map(t => t.innerText.trim().slice(0, 200)).filter(t => t.length > 0).slice(0, 20);
    })()
    """)
    print(f"Profile page: {json.dumps(ig_profile, indent=2)}")
    
    # Look for Message button
    ig_message_btn = await evaluate(ig_ws, """
    (() => {
        const buttons = Array.from(document.querySelectorAll('button, div[role="button"], a[role="button"]'));
        const msgBtn = buttons.find(b => {
            const text = b.innerText.toLowerCase();
            return text.includes('message') || text.includes('contact') || text.includes('dm');
        });
        if (msgBtn) { msgBtn.click(); return 'clicked_message'; }
        return 'no_message_button';
    })()
    """)
    print(f"Message button: {ig_message_btn}")
    await asyncio.sleep(2)
    
    # ============ WHATSAPP: Search directly by phone in main search ============
    print("\n=== WHATSAPP: Search by phone in main search ===")
    wa_search = await evaluate(wa_ws, """
    (() => {
        const inputs = Array.from(document.querySelectorAll('input[aria-label="Search or start a new chat"]'));
        const inp = inputs.find(i => i.offsetParent !== null);
        if (inp) {
            inp.focus();
            inp.value = '+34 661 571 463';
            inp.dispatchEvent(new Event('input', {bubbles: true}));
            inp.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
            return 'searched_phone';
        }
        return 'no_input';
    })()
    """)
    print(f"Search phone: {wa_search}")
    await asyncio.sleep(3)
    
    # Check if chat appears
    wa_chat = await evaluate(wa_ws, """
    (() => {
        const chats = Array.from(document.querySelectorAll('[role="listitem"], [role="button"][tabindex], div[tabindex="-1"]'));
        const target = chats.find(c => c.innerText.includes('661 571 463') || c.innerText.includes('661571463') || c.innerText.includes('Shudokan'));
        if (target) { target.click(); return 'clicked_chat'; }
        // Also check all visible text
        const allText = Array.from(document.querySelectorAll('div')).map(d => d.innerText.trim()).filter(t => t.length > 0 && t.length < 200);
        return allText.slice(0, 30);
    })()
    """)
    print(f"Chat search: {json.dumps(wa_chat, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
