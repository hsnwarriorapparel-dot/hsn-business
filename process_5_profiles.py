import asyncio
import websockets
import json

ws_url = 'ws://127.0.0.1:9222/devtools/page/C855E1B3EA6C1D18350ADECF657FE7FC'

# 5 target profiles from post comments - gym/club accounts
TARGET_PROFILES = [
    'phuketfightclub',      # gym
    'bjj_machine',          # gym/academy
    'katie.coro.bjj',       # practitioner (might have email)
    'gabriel_phuketfightclub',  # gym affiliated
    'goldpanelsport',       # sports club
]

async def process_profile(ws, profile, profile_num):
    print(f'\n=== PROFILE {profile_num}: @{profile} ===')
    
    # Navigate to profile
    print(f'1. Navigating to /{profile}/...')
    await ws.send(json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': f'https://www.instagram.com/{profile}/'}}))
    for _ in range(15):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 1:
            break
    
    await asyncio.sleep(5)
    
    # Check for email in profile bio
    print('2. Checking for email in bio...')
    expr_email = r'(function() { const allText = document.body.innerText; const emails = allText.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g); return JSON.stringify(emails || []); })()'
    await ws.send(json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': expr_email, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 2:
            emails = json.loads(data['result'].get('value', '[]'))
            print(f'   Emails found: {emails}')
            break
    
    # Check Follow button status
    print('3. Checking Follow button...')
    expr_follow = r'(function() { const btns = document.querySelectorAll("button"); for (const btn of btns) { const text = (btn.innerText || "").toLowerCase(); if (text === "follow" || text === "following" || text === "requested" || text === "seguir" || text === "siguiendo") { return {text: btn.innerText, class: btn.className}; } } return {text: "not found"}; })()'
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
    
    # Try Ctrl+Enter to send
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
    
    # Check for email again (maybe in contact options)
    print('8. Final email check...')
    await ws.send(json.dumps({'id': 8, 'method': 'Runtime.evaluate', 'params': {'expression': expr_email, 'returnByValue': True}}))
    for _ in range(10):
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == 8:
            emails = json.loads(data['result'].get('value', '[]'))
            print(f'   Emails: {emails}')
            break
    
    return emails

async def main():
    ws = await websockets.connect(ws_url)
    await ws.send(json.dumps({'id': 0, 'method': 'Runtime.enable'}))
    await ws.recv()
    
    all_emails = []
    for i, profile in enumerate(TARGET_PROFILES, 1):
        emails = await process_profile(ws, profile, i)
        all_emails.extend(emails)
        await asyncio.sleep(3)
    
    print('\n=== SUMMARY ===')
    print(f'Total emails found: {len(all_emails)}')
    print(f'Emails: {all_emails}')
    
    await ws.close()

asyncio.run(main())