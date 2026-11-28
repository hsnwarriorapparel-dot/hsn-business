import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

# Gyms with known websites from bjj.space
GYM_SITES = [
    {'handle': 'gorilla_bjj_academy', 'url': 'https://www.gorillabjj.com'},
    {'handle': 'checkmatbristol', 'url': 'https://instagram.com/p/DMxYbKIId0n'},  # Instagram post
    {'handle': 'combatevolutionbjj', 'url': 'https://www.instagram.com/combatevolutionbjj'},  # IG only
    {'handle': 'backbone_bjj', 'url': 'https://www.backbonebjj.com'},
    {'handle': 'groundstonebjj', 'url': 'https://www.groundstonebjj.com'},
    {'handle': 'baysidebjj', 'url': 'https://www.baysidebjj.com'},
    {'handle': 'cquencebjj', 'url': 'https://norcobjj.com/schedule/'},
    {'handle': 'bellaartjiu', 'url': 'https://www.instagram.com/bellaartjiu'},
    {'handle': 'wiltshirebjjacademymarlborough', 'url': 'https://www.wiltshirebjj.academy'},
]

async def check_website(ws, gym):
    handle = gym['handle']
    url = gym['url']
    print(f'\n=== {handle} -> {url} ===')
    
    await ws.send(json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': url}}))
    for _ in range(20):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 1:
            break
    
    await asyncio.sleep(5)
    
    # Get page text
    expr = r'(function() { const allText = document.body.innerText; return allText; })()'
    await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            text = data['result'].get('value', '')
            lines = text.split('\n')
            contact = [l.strip() for l in lines if any(kw in l.lower() for kw in ['whatsapp', 'wa.me', 'phone', 'call', 'contact', '+', 'mobile', 'tel:', 'zap', 'email', '@'])]
            print(f'  Contact info: {contact[:15]}')
            break

async def main():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 0, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    for gym in GYM_SITES:
        await check_website(ws, gym)
        await asyncio.sleep(3)
    
    await ws.close()

asyncio.run(main())