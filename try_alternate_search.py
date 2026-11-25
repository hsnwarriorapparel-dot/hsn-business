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
    
    # ============ INSTAGRAM: Search by club name "ROJE SHUDOKAN" ============
    print("=== INSTAGRAM: Search 'ROJE SHUDOKAN' ===")
    ig_search = await evaluate(ig_ws, """
    (() => {
        const inputs = Array.from(document.querySelectorAll('input[placeholder="Search"], input[placeholder="Search..."]'));
        const searchInput = inputs.find(i => i.offsetParent !== null);
        if (searchInput) {
            searchInput.focus();
            searchInput.value = 'ROJE SHUDOKAN';
            searchInput.dispatchEvent(new Event('input', {bubbles: true}));
            searchInput.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
            searchInput.dispatchEvent(new KeyboardEvent('keyup', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
            return 'typed_and_entered';
        }
        return 'no_input';
    })()
    """)
    print(f"Search: {ig_search}")
    await asyncio.sleep(4)
    
    # Check results
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
    print(json.dumps(ig_results, indent=2))
    
    # Try "Club Deportivo ROJE"
    print("\n=== INSTAGRAM: Search 'Club Deportivo' ===")
    ig_search2 = await evaluate(ig_ws, """
    (() => {
        const inputs = Array.from(document.querySelectorAll('input[placeholder="Search"], input[placeholder="Search..."]'));
        const searchInput = inputs.find(i => i.offsetParent !== null);
        if (searchInput) {
            searchInput.focus();
            searchInput.value = 'Club Deportivo';
            searchInput.dispatchEvent(new Event('input', {bubbles: true}));
            searchInput.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
            searchInput.dispatchEvent(new KeyboardEvent('keyup', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
            return 'typed_and_entered';
        }
        return 'no_input';
    })()
    """)
    print(f"Search: {ig_search2}")
    await asyncio.sleep(4)
    
    ig_results2 = await evaluate(ig_ws, """
    (() => {
        const elements = Array.from(document.querySelectorAll('[role="option"], [role="button"], button, div[tabindex="0"], a, div.x1i10hfl.x1qjc9v5'));
        return elements.map(e => ({
            text: e.innerText.trim().slice(0, 100),
            tag: e.tagName,
            class: e.className.slice(0, 60)
        })).filter(e => e.text.length > 0).slice(0, 30);
    })()
    """)
    print(json.dumps(ig_results2, indent=2))
    
    # ============ WHATSAPP: Check state after contact save ============
    print("\n=== WHATSAPP: State After Contact Save ===")
    wa_state = await evaluate(wa_ws, """
    (() => {
        const buttons = Array.from(document.querySelectorAll('button, div[role="button"]'));
        const inputs = Array.from(document.querySelectorAll('input, div[contenteditable="true"]'));
        return {
            buttons: buttons.map(b => ({text: b.innerText.trim().slice(0,60), aria: b.getAttribute('aria-label')||'', class: b.className.slice(0,50)})).filter(b => b.text),
            inputs: inputs.map(i => ({tag: i.tagName, placeholder: i.getAttribute('placeholder')||'', aria: i.getAttribute('aria-label')||'', role: i.getAttribute('role')||'', 'data-tab': i.getAttribute('data-tab')||'', class: i.className.slice(0,50)})).filter(i => i.placeholder || i.aria || i.role || i['data-tab'])
        };
    })()
    """)
    print(json.dumps(wa_state, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
