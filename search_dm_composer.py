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
    
    # Click Send message again
    ig_new = await evaluate(ig_ws, """
    (() => {
        const buttons = Array.from(document.querySelectorAll('button, div[role="button"], a[role="button"]'));
        const newBtn = buttons.find(b => {
            const text = b.innerText.toLowerCase().trim();
            return text === 'send message';
        });
        if (newBtn) { newBtn.click(); return 'clicked_send_message'; }
        return 'no_send_message';
    })()
    """)
    print(f"Send message: {ig_new}")
    await asyncio.sleep(2)
    
    # Search for "Shudokan" (broader)
    ig_search = await evaluate(ig_ws, """
    (() => {
        const inputs = Array.from(document.querySelectorAll('input[placeholder*="Search"], input[aria-label*="Search"], div[contenteditable="true"][role="textbox"]'));
        const inp = inputs.find(i => i.offsetParent !== null);
        if (inp) {
            inp.focus();
            inp.value = 'Shudokan';
            inp.innerText = 'Shudokan';
            inp.dispatchEvent(new Event('input', {bubbles: true}));
            inp.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
            return 'searched_shudokan';
        }
        return 'no_input';
    })()
    """)
    print(f"Search Shudokan: {ig_search}")
    await asyncio.sleep(4)
    
    # Check search results
    ig_results = await evaluate(ig_ws, """
    (() => {
        const elements = Array.from(document.querySelectorAll('[role="option"], [role="button"], button, div[tabindex="0"], a, div.x1i10hfl.x1qjc9v5'));
        return elements.map(e => ({
            text: e.innerText.trim().slice(0, 100),
            tag: e.tagName,
            class: e.className.slice(0, 60)
        })).filter(e => e.text.length > 0).slice(0, 30);
    })()
    """)
    print(f"Results: {json.dumps(ig_results, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
