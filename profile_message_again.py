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
    
    # Navigate to profile
    print("=== INSTAGRAM: Navigate to @shudokan.roje Profile ===")
    ig_nav = await evaluate(ig_ws, """
    (() => {
        window.location.href = 'https://instagram.com/shudokan.roje';
        return 'navigated';
    })()
    """)
    print(f"Navigate: {ig_nav}")
    await asyncio.sleep(4)
    
    # Click Message button
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
    
    # Check composer state - look for ALL clickable elements
    print("=== INSTAGRAM: Composer Elements ===")
    ig_composer = await evaluate(ig_ws, """
    (() => {
        const all = Array.from(document.querySelectorAll('button, div[role="button"], svg, [data-testid]'));
        return all.map(el => ({
            tag: el.tagName,
            text: el.innerText?.trim().slice(0,50) || '',
            aria: el.getAttribute('aria-label') || '',
            testid: el.getAttribute('data-testid') || '',
            title: el.getAttribute('title') || '',
            class: el.className?.slice(0,60) || '',
            type: el.getAttribute('type') || '',
            'data-visual-completion': el.getAttribute('data-visual-completion') || ''
        })).filter(e => e.text || e.aria || e.testid || e.title || e['data-visual-completion']).slice(0, 40);
    })()
    """)
    print(json.dumps(ig_composer, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
