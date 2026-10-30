#!/usr/bin/env python3
"""Activate the WhatsApp tab WITHOUT reloading it, then screenshot the desktop."""
import json, subprocess, sys, time, urllib.request
import websocket

CDP = 'http://127.0.0.1:9222'
tabs = json.load(urllib.request.urlopen(CDP + '/json/list', timeout=10))
wa = [t for t in tabs if 'web.whatsapp.com' in t.get('url', '') and t.get('type') == 'page']
if not wa:
    print('NO_WA_TAB'); sys.exit(2)
wid = wa[0]['id']
print('activating WA tab', wid)

ver = json.load(urllib.request.urlopen(CDP + '/json/version', timeout=10))
ws = websocket.create_connection(ver['webSocketDebuggerUrl'], timeout=30, suppress_origin=True)
ws.send(json.dumps({'id': 1, 'method': 'Target.activateTarget', 'params': {'targetId': wid}}))
try:
    for _ in range(20):
        m = json.loads(ws.recv())
        if m.get('id') == 1:
            print('activateTarget ->', m.get('result', m.get('error')))
            break
except Exception as e:
    print('activate err', str(e)[:100])
ws.close()

time.sleep(4)
subprocess.run(['/home/ubuntu/.hermes/tools/ffmpeg-9.0.1-linux-arm64/bin/ffmpeg', '-f', 'x11grab',
                '-video_size', '1920x1080', '-i', ':21', '-frames:v', '1', '-y',
                '/home/ubuntu/wa_desk_active.png'],
               env={'DISPLAY': ':21', 'XAUTHORITY': '/home/ubuntu/.hermes/bot-desktop/Xauthority',
                    'PATH': '/usr/bin:/bin'}, capture_output=True)
print('screenshot written')
