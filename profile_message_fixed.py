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
    
    # Click Message button (should already be on profile from previous)
    ig_msg = await evaluate(ig_ws, """
    (() => {
        const buttons = Array.from(document.querySelectorAll('button, div[role="button"], a[role="button"]'));
        const msgBtn = buttons.find(b => {
            const text = b.innerText.trim();
            return text === 'Message' || text === 'Mensaje';
        });
        if (msgBtn) { msgBtn.click(); return 'clicked_message'; }
        return 'no_message_button';
    })()
    """)
    print(f"Message button: {ig_msg}")
    await asyncio.sleep(3)
    
    # Check composer elements - fixed
    print("=== INSTAGRAM: Composer Elements ===")
    ig_composer = await evaluate(ig_ws, """
    (() => {
        const all = Array.from(document.querySelectorAll('button, div[role="button"], svg, [data-testid]'));
        return all.map(el => {
            const cls = el.className || '';
            return {
                tag: el.tagName,
                text: el.innerText?.trim().slice(0,50) || '',
                aria: el.getAttribute('aria-label') || '',
                testid: el.getAttribute('data-testid') || '',
                title: el.getAttribute('title') || '',
                class: typeof cls === 'string' ? cls.slice(0,60) : '',
                type: el.getAttribute('type') || ''
            };
        }).filter(e => e.text || e.aria || e.testid || e.title).slice(0, 50);
    })()
    """)
    print(json.dumps(ig_composer, indent=2))
    
    # Find message input
    print("\n=== INSTAGRAM: Message Input ===")
    ig_input = await evaluate(ig_ws, """
    (() => {
        const inputs = Array.from(document.querySelectorAll('textarea, div[contenteditable="true"]'));
        return inputs.map(i => ({
            tag: i.tagName,
            placeholder: i.getAttribute('placeholder') || '',
            aria: i.getAttribute('aria-label') || '',
            role: i.getAttribute('role') || '',
            class: (i.className || '').slice(0,60),
            visible: i.offsetParent !== null
        })).filter(i => i.visible);
    })()
    """)
    print(json.dumps(ig_input, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
