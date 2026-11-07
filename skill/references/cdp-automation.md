# CDP Automation Reference

Complete patterns for automating Gmail, Instagram, and WhatsApp via Chrome DevTools Protocol (CDP) on the existing browser session (work-profile-1).

## Prerequisites
- Xvnc :21 running
- Chromium snap with `--user-data-dir=/home/ubuntu/work-profile-1 --remote-debugging-port=9222`
- Gmail, Instagram, WhatsApp Web all logged in
- CDP accessible at `http://localhost:9222`
- Hermes Python: `/home/ubuntu/.hermes/tools/python-3.14.7+*/bin/python3` (has `websockets`)

## Core CDP Pattern
```python
import asyncio
import websockets
import json
import requests

async def cdp_session(tab_ws_url):
    async with websockets.connect(tab_ws_url) as ws:
        # Enable Runtime
        await ws.send(json.dumps({'id': 1, 'method': 'Runtime.enable'}))
        while True:
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == 1:
                break
        
        # Evaluate expression with proper event polling
        await ws.send(json.dumps({
            'id': cmd_id,
            'method': 'Runtime.evaluate',
            'params': {
                'expression': js_code,
                'awaitPromise': True,
                'returnByValue': True
            }
        }))
        while True:
            resp = await ws.recv()
            data = json.loads(resp)
            if 'id' in data and data['id'] == cmd_id:
                return data
            elif 'method' in data:
                pass  # Ignore events
```

## Gmail Automation (WORKING - 50/day)

### Tab Discovery
```python
resp = requests.get('http://localhost:9222/json/list')
pages = resp.json()
gmail_tab = next(p for p in pages if 'mail.google.com' in p.get('url', '') and p['type'] == 'page')
```

### Send Email Steps
1. **Click Compose**: `document.querySelector('[gh="cm"]').click()`
2. **Fill To**: `document.querySelector('[name="to"]').value = email` + Enter key
3. **Fill Subject**: `document.querySelector('[name="subjectbox"]').value = subject`
4. **Fill Body**: `document.querySelector('[aria-label="Message Body"]').innerText = body`
5. **Click Send**: `document.querySelector('[aria-label*="Send"]').click()`

### Key Fixes
- Use `returnByValue: true` + `awaitPromise: true` + poll for `id` match
- React buttons need `Input.dispatchMouseEvent` with coordinates from `getBoundingClientRect()`
- Rate limit: 5s between sends

## Instagram Automation (PARTIAL - 20/day)

### Tab Discovery
```python
ig_tab = next(p for p in pages if 'instagram.com' in p.get('url', '') and p['type'] == 'page')
```

### Send DM via Profile (WORKING)
1. **Navigate to profile**: `Page.navigate` to `https://www.instagram.com/{username}/`
2. **Click Message button**: CDP click at coordinates (x=843, y=244) - found via `getBoundingClientRect()` on button with text "Message"
3. **Type message**: `document.querySelector('[role="textbox"]').innerText = message`
4. **Click Send**: CDP click at coordinates (x=1142, y=725) - found on Send button

### Limitations
- Profile URL mapping for new leads: need to guess username from club name
- Search in DM inbox filters existing conversations, not new users
- Split-view thread panel composer not reliably accessible via CDP

## WhatsApp Automation (PARTIAL - 10/day)

### Tab Discovery
```python
wa_tab = next(p for p in pages if 'web.whatsapp.com' in p.get('url', '') and p['type'] == 'page')
```

### Send Message
1. **Search contact**: `document.querySelector('[data-testid="chat-list-search"]').value = phone`
2. **Click result**: CDP click at approximate position (x=400, y=300)
3. **Type message**: `document.querySelector('[data-testid="conversation-compose-box-input"]').innerText = message`
4. **Click Send**: `document.querySelector('[data-testid="compose-btn-send"]').click()`

### Limitations
- Contact search needs phone format normalization (strip spaces, add country code)
- Chat list search may not find unsaved contacts reliably

## React Button Handling (CRITICAL)

**Problem**: React buttons (Gmail, IG, WA) don't respond to `.click()` or `dispatchEvent('click')`

**Solution**: Use CDP `Input.dispatchMouseEvent` with coordinates:
```python
# Get button position
rect = btn.getBoundingClientRect()
x, y = rect.left + rect.width/2, rect.top + rect.height/2

# CDP click
await ws.send(json.dumps({
    'method': 'Input.dispatchMouseEvent',
    'params': {'type': 'mousePressed', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1}
}))
# ... wait for id ...
await ws.send(json.dumps({
    'method': 'Input.dispatchMouseEvent',
    'params': {'type': 'mouseReleased', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1}
}))
```

## Event Polling Pattern (CRITICAL)

**Problem**: `Runtime.evaluate` returns `Runtime.executionContextCreated` events, not the result

**Solution**: Poll for matching `id`:
```python
async def cdp_eval(ws, expr, cmd_id):
    await ws.send(json.dumps({
        'id': cmd_id,
        'method': 'Runtime.evaluate',
        'params': {'expression': expr, 'awaitPromise': True, 'returnByValue': True}
    }))
    while True:
        resp = await ws.recv()
        data = json.loads(resp)
        if 'id' in data and data['id'] == cmd_id:
            return data
        elif 'method' in data:
            pass  # Ignore events
```

## Rate Limits (Enforced in Code)
| Channel | Limit | Delay |
|---------|-------|-------|
| Email | 100/day | 5s |
| IG DM | 50/day | 8s |
| WhatsApp | 10/day | 10s |

## Troubleshooting
| Issue | Fix |
|-------|-----|
| `websockets` ModuleNotFoundError | Use Hermes Python: `/home/ubuntu/.hermes/tools/python-3.14.7+*/bin/python3` |
| CDP returns events not results | Use `returnByValue: true` + poll for `id` match |
| React buttons don't click | Use `Input.dispatchMouseEvent` with coordinates |
| IG search finds existing convos | Navigate to profile URL directly |
| Cron uses wrong Python | Wrapper script sets PATH to Hermes Python |
| `websockets` not in system Python | Install in Hermes Python or use hermes Python |

## Coordinate Discovery
```python
# Find button and get coordinates
expr = '''
(function() {
    var btn = document.querySelector('selector');
    if (btn) {
        var rect = btn.getBoundingClientRect();
        return {x: rect.left + rect.width/2, y: rect.top + rect.height/2};
    }
    return null;
})()
'''
result = await cdp_eval(ws, expr, cmd_id)
pos = result['result']['result']['value']
```

## Files
- `/home/ubuntu/email_sender_cdp.py` - Gmail automation (working)
- `/home/ubuntu/ig_dm_sender_cdp.py` - Instagram automation (partial)
- `/home/ubuntu/wa_sender_cdp.py` - WhatsApp automation (partial)
- `/home/ubuntu/daily_automation_full.py` - Master orchestrator
- `/home/ubuntu/daily_automation_cron.sh` - Cron wrapper