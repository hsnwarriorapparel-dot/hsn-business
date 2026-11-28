import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

# Gyms with known emails and Instagram handles from search
GYM_PROFILES = [
    {'handle': 'escapebjjacademy', 'email': 'escapebjjacademy@gmail.com'},
    {'handle': 'vaughan.bjj', 'email': 'vaughan.bjj@gmail.com'},
    {'handle': 'safeguard.bjj', 'email': 'safeguardmartialartstx@gmail.com'},
    {'handle': 'bittencourt_bjj', 'email': 'brenobittencourtjiujitsu@gmail.com'},
    {'handle': 'theacademy.bjj', 'email': 'theacademyofjiujitsu@gmail.com'},
    {'handle': 'tmbjjacademy', 'email': 'Tmbjjacademy@gmail.com'},
    {'handle': 'wiltshirebjjacademymarlborough', 'email': 'wiltshirebjjacademy@gmail.com'},
    {'handle': 'theacademyofbjj', 'email': 'matherleyj@gmail.com'},
    {'handle': 'matrixbjjacademy', 'email': 'Leomatrixbjj@gmail.com'},
    {'handle': 'gorilla_bjj_academy', 'email': 'gorillabjjacademy@gmail.com'},
]

async def process_gym(ws, gym, gym_num):
    handle = gym['handle']
    expected_email = gym['email']
    print(f'\n=== GYM {gym_num}: @{handle} (expected: {expected_email}) ===')
    
    # Navigate to profile
    print(f'1. Navigating to /{handle}/...')
    await ws.send(json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': f'https://www.instagram.com/{handle}/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 1:
            break
    
    await asyncio.sleep(5)
    
    # Check for email in profile
    print('2. Checking for email in profile...')
    expr_email = r'(function() { const allText = document.body.innerText; const emails = allText.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g); return JSON.stringify(emails || []); })()'
    await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': expr_email, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            emails = json.loads(data['result'].get('value', '[]'))
            print(f'   Emails found: {emails}')
            break
    
    # Check Follow button
    print('3. Checking Follow button...')
    expr_follow = r'(function() { const btns = document.querySelectorAll("button"); for (const btn of btns) { const text = (btn.innerText || "").toLowerCase(); if (text === "follow" || text === "following" || text === "requested" || text === "seguir") { return {text: btn.innerText}; } } return {text: "not found"}; })()'
    await ws.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {'expression': expr_follow, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 3:
            print(f'   Follow status: {data}')
            break
    
    # Click Follow if not following
    print('4. Clicking Follow...')
    expr_click_follow = r'(function() { const btns = document.querySelectorAll("button"); for (const btn of btns) { const text = (btn.innerText || "").toLowerCase(); if (text === "follow" || text === "seguir") { btn.click(); return {clicked: true, text: btn.innerText}; } } return {clicked: false}; })()'
    await ws.send(json.dumps({'id': 4, 'method': 'Runtime.evaluate', 'params': {'expression': expr_click_follow, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 4:
            print(f'   Follow click: {data}')
            break
    
    await asyncio.sleep(2)
    
    # Click Message button
    print('5. Clicking Message...')
    expr_msg = r'(function() { const btns = document.querySelectorAll("button, div[role=\"button\"]"); for (const btn of btns) { const text = (btn.innerText || "").toLowerCase(); if (text === "message") { btn.click(); return {clicked: true, text: btn.innerText}; } } return {clicked: false}; })()'
    await ws.send(json.dumps({'id': 5, 'method': 'Runtime.evaluate', 'params': {'expression': expr_msg, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 5:
            print(f'   Message click: {data}')
            break
    
    await asyncio.sleep(3)
    
    # Type DM
    print('6. Typing DM...')
    dm_text = "Hi! We're HSN Warrior Apparels from Sialkot, Pakistan - manufacturer of BJJ/Judo/Karate/MMA gear. Interested in wholesale/OEM? DM for catalog."
    expr_dm = f'(function() {{ const textarea = document.querySelector("div[role=\\"textbox\\"][contenteditable=\\"true\\"].xzsf02u"); if (textarea) {{ textarea.focus(); textarea.innerText = `{dm_text.replace("`", "\\\\`").replace("${", "\\\\${")}`; textarea.dispatchEvent(new Event("input", {{bubbles: true}})); return true; }} return false; }})()'
    await ws.send(json.dumps({'id': 6, 'method': 'Runtime.evaluate', 'params': {'expression': expr_dm, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 6:
            print(f'   Type DM: {data}')
            break
    
    await asyncio.sleep(1)
    
    # Send DM with Ctrl+Enter
    print('7. Sending DM (Ctrl+Enter)...')
    expr_send = r'(function() { const textarea = document.querySelector("div[role=\"textbox\"][contenteditable=\"true\"].xzsf02u"); if (textarea) { textarea.focus(); textarea.dispatchEvent(new KeyboardEvent("keydown", {key: "Enter", ctrlKey: true, bubbles: true})); return true; } return false; })()'
    await ws.send(json.dumps({'id': 7, 'method': 'Runtime.evaluate', 'params': {'expression': expr_send, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 7:
            print(f'   Send: {data}')
            break
    
    await asyncio.sleep(2)
    
    # Verify DM sent by checking inbox
    print('8. Verifying DM sent...')
    await ws.send(json.dumps({'id': 8, 'method': 'Page.navigate', 'params': {'url': 'https://www.instagram.com/direct/inbox/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 8:
            break
    
    await asyncio.sleep(4)
    
    expr_verify = f'(function() {{ const threads = document.querySelectorAll("div[role=\\"listitem\\"], div[role=\\"button\\"]"); const results = []; threads.forEach(t => {{ const text = t.innerText; if (text && text.toLowerCase().includes("{handle.lower()}")) results.push(text.substring(0, 200)); }}); return JSON.stringify(results); }})()'
    await ws.send(json.dumps({'id': 9, 'method': 'Runtime.evaluate', 'params': {'expression': expr_verify, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 9:
            print(f'   Inbox verification: {data}')
            break
    
    # Return emails found
    return emails

async def main():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 0, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    all_emails = []
    for i, gym in enumerate(GYM_PROFILES, 1):
        emails = await process_gym(ws, gym, i)
        all_emails.extend(emails)
        if len(all_emails) >= 5:
            break
        await asyncio.sleep(3)
    
    print('\n=== SUMMARY ===')
    print(f'Total emails found: {len(all_emails)}')
    print(f'Emails: {all_emails}')
    
    await ws.close()

asyncio.run(main())