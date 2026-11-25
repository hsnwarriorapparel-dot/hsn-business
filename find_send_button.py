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
    
    # Find ALL buttons and clickable elements
    print("=== INSTAGRAM: All Buttons ===")
    all_buttons = await evaluate(ig_ws, """
    (() => {
        const buttons = Array.from(document.querySelectorAll('button, div[role="button"], svg, [data-testid]'));
        return buttons.map(b => ({
            tag: b.tagName,
            text: b.innerText.trim().slice(0,50),
            aria: b.getAttribute('aria-label')||'',
            testid: b.getAttribute('data-testid')||'',
            class: b.className.slice(0,60),
            title: b.getAttribute('title')||''
        })).filter(b => b.text || b.aria || b.testid || b.title);
    })()
    """)
    print(json.dumps(all_buttons, indent=2))
    
    # Try pressing Enter in the message input
    print("\n=== INSTAGRAM: Press Enter in Message Input ===")
    ig_enter = await evaluate(ig_ws, """
    (() => {
        const inputs = Array.from(document.querySelectorAll('div[contenteditable="true"][role="textbox"]'));
        const inp = inputs.find(i => i.offsetParent !== null);
        if (inp) {
            inp.focus();
            inp.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
            inp.dispatchEvent(new KeyboardEvent('keyup', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
            return 'pressed_enter';
        }
        return 'no_input';
    })()
    """)
    print(f"Enter: {ig_enter}")
    await asyncio.sleep(2)
    
    # Check if message sent (look for message in thread)
    ig_check = await evaluate(ig_ws, """
    (() => {
        const messages = Array.from(document.querySelectorAll('[role="log"], [data-testid="message-thread"], div[role="list"]'));
        return messages.map(m => m.innerText.trim().slice(0,200)).filter(m => m.length > 0).slice(0, 10);
    })()
    """)
    print(f"Thread check: {json.dumps(ig_check, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
