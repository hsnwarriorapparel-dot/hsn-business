import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

# City-specific gym searches - try hashtags
CITY_HASHTAGS = [
    'bjjhouston',
    'bjjlondon',
    'bjjnewyork',
    'bjjlosangeles',
    'bjjchicago',
    'bjjmiami',
    'bjjdallas',
    'bjjtoronto',
    'bjjsydney',
    'bjjmelbourne',
    'jiujitsuhouston',
    'jiujitsulondon',
    'jiujitsunewyork',
]

async def check_hashtag_posts(ws, hashtag):
    print(f'\n=== #{hashtag} ===')
    
    # Navigate to hashtag
    await ws.send(json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': f'https://www.instagram.com/explore/tags/{hashtag}/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 1:
            break
    
    await asyncio.sleep(5)
    
    # Get post links
    expr = r'(function() { const links = document.querySelectorAll("a[href^=\"/p/\"]"); const urls = []; links.forEach(l => urls.push(l.href)); return JSON.stringify(urls.slice(0, 5)); })()'
    await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            urls = json.loads(data['result'].get('value', '[]'))
            print(f'   Post URLs: {urls}')
            break
    
    # Check first post for profiles
    emails_found = []
    for url in urls[:2]:
        print(f'   Checking post: {url}')
        await ws.send(json.dumps({'id': 3, 'method': 'Page.navigate', 'params': {'url': url}}))
        for _ in range(15):
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 3:
                break
        
        await asyncio.sleep(4)
        
        # Get all profile links from post page
        expr2 = r'(function() { const links = []; document.querySelectorAll("a[href^=\"/\"]").forEach(a => { const href = a.getAttribute("href"); if (href && href.match(/^\/[^\/]+\/?$/)) links.push(href); }); return JSON.stringify([...new Set(links)].slice(0, 20)); })()'
        await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': expr2, 'returnByValue': True}}))
        for _ in range(10):
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 4:
                profiles = json.loads(data['result'].get('value', '[]'))
                print(f'   Profiles from post: {profiles}')
                
                # Check each profile for email
                for p in profiles:
                    profile_name = p.strip('/')
                    if profile_name not in ['reels', 'explore', 'popular', 'hsnwarriorapparel']:
                        emails = await check_profile_email(ws, profile_name)
                        emails_found.extend(emails)
                break
    
    return emails_found

async def check_profile_email(ws, profile):
    print(f'     Checking @{profile}...')
    await ws.send(json.dumps({'id': 10, 'method': 'Page.navigate', 'params': {'url': f'https://www.instagram.com/{profile}/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 10:
            break
    
    await asyncio.sleep(3)
    
    expr = r'(function() { const allText = document.body.innerText; const emails = allText.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g); return JSON.stringify(emails || []); })()'
    await ws.send(json.dumps({'id': 11, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 11:
            emails = json.loads(data['result'].get('value', '[]'))
            if emails:
                print(f'       EMAILS: {emails}')
            return emails
    
    return []

async def main():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 0, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    all_emails = []
    for hashtag in CITY_HASHTAGS:
        emails = await check_hashtag_posts(ws, hashtag)
        all_emails.extend(emails)
        if len(all_emails) >= 5:
            break
        await asyncio.sleep(3)
    
    print('\n=== SUMMARY ===')
    print(f'Total emails found: {len(all_emails)}')
    print(f'Emails: {all_emails}')
    
    await ws.close()

asyncio.run(main())