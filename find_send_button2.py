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
    
    # Find ALL elements with send-related attributes
    print("=== INSTAGRAM: Find Send Button ===")
    send_elements = await evaluate(ig_ws, """
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
            class: el.className?.slice(0,60) || '',
            type: el.getAttribute('type') || ''
        })).slice(0, 20);
    })()
    """)
    print(json.dumps(send_elements, indent=2))
    
    # Also find elements near the message input
    print("\n=== INSTAGRAM: Elements Near Message Input ===")
    near_input = await evaluate(ig_ws, """
    (() => {
        const inputs = Array.from(document.querySelectorAll('div[contenteditable="true"][role="textbox"]'));
        const inp = inputs.find(i => i.offsetParent !== null);
        if (!inp) return 'no_input';
        
        // Get parent and siblings
        const parent = inp.parentElement;
        const siblings = parent ? Array.from(parent.querySelectorAll('*')) : [];
        return siblings.map(el => ({
            tag: el.tagName,
            text: el.innerText?.trim().slice(0,50) || '',
            aria: el.getAttribute('aria-label') || '',
            testid: el.getAttribute('data-testid') || '',
            class: el.className?.slice(0,60) || ''
        })).filter(e => e.text || e.aria || e.testid);
    })()
    """)
    print(json.dumps(near_input, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
