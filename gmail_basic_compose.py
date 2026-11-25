import asyncio
import json
import websockets
import aiohttp

async def get_gmail_ws():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://127.0.0.1:9222/json') as resp:
            pages = await resp.json()
            for p in pages:
                if 'mail.google.com' in p.get('url', ''):
                    return p.get('webSocketDebuggerUrl')
    return None

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
    gmail_ws = await get_gmail_ws()
    
    if not gmail_ws:
        print("Gmail tab not found")
        return
    
    print(f"Gmail WS: {gmail_ws}")
    await send_cdp(gmail_ws, "Runtime.enable")
    
    # Find compose in basic HTML
    print("=== GMAIL BASIC: Find Compose ===")
    gm_compose = await evaluate(gmail_ws, """
    (() => {
        const links = Array.from(document.querySelectorAll('a[href*="compose"], a[href*="comp"]'));
        return links.map(l => ({
            href: l.getAttribute('href') || '',
            text: l.innerText.trim(),
            class: (l.className || '').slice(0,60)
        }));
    })()
    """)
    print(f"Compose links: {json.dumps(gm_compose, indent=2)}")
    
    # Try clicking compose via href
    if gm_compose and isinstance(gm_compose, dict) and gm_compose.get('result', {}).get('value'):
        links = gm_compose['result']['value']
        if links:
            href = links[0]['href']
            print(f"Navigating to: {href}")
            await evaluate(gmail_ws, f"""
            (() => {{
                window.location.href = '{href}';
                return 'navigated';
            }})()
            """)
            await asyncio.sleep(3)
    
    # Check compose page
    gm_info = await evaluate(gmail_ws, """
    (() => ({
        title: document.title,
        url: window.location.href
    }))()
    """)
    print(f"Page: {json.dumps(gm_info, indent=2)}")
    
    # Find form fields
    gm_form = await evaluate(gmail_ws, """
    (() => {
        const inputs = Array.from(document.querySelectorAll('input, textarea'));
        return inputs.map(i => ({
            name: i.getAttribute('name') || '',
            type: i.getAttribute('type') || '',
            placeholder: i.getAttribute('placeholder') || '',
            class: (i.className || '').slice(0,60)
        })).filter(i => i.name || i.placeholder);
    })()
    """)
    print(f"Form fields: {json.dumps(gm_form, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
