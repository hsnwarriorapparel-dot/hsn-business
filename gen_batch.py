#!/usr/bin/env python3
import sys, time, json, base64
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import *

def count_blobs(ws):
    v = js_eval(ws, '''(() => document.querySelectorAll('img[src^="blob:"]').length)()''')
    try: return int(v)
    except: return 0

def gen(prompt, out_path):
    tabs = get_tabs()
    ais = [t for t in tabs if 'gemini.google' in t['url'] and t['type']=='page']
    if not ais:
        print("no gemini tab"); return False
    ws = connect(ais[0])
    cdp = make_cdp(ws)
    cdp("Page.bringToFront")
    time.sleep(2)
    before = count_blobs(ws)
    # click input + type + enter
    v = js_eval(ws, '''(() => {
      const inp = document.querySelector('rich-textarea div.ql-editor, .ql-editor, rich-textarea, textarea');
      if (!inp) return null;
      const r = inp.getBoundingClientRect();
      return JSON.stringify({x: Math.round(r.x + r.width/2), y: Math.round(r.y + Math.min(50, r.height/2))});
    })()''')
    if not v:
        print("no input"); ws.close(); return False
    p = json.loads(v)
    cdp("Input.dispatchMouseEvent", {"type": "mousePressed", "x": p['x'], "y": p['y'], "button": "left", "clickCount": 1})
    cdp("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": p['x'], "y": p['y'], "button": "left", "clickCount": 1})
    time.sleep(0.8)
    cdp("Input.insertText", {"text": prompt})
    time.sleep(0.8)
    cdp("Input.dispatchKeyEvent", {"type": "rawKeyDown", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13})
    cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13})
    # wait for blob count to increase
    for i in range(30):
        time.sleep(5)
        now = count_blobs(ws)
        if now > before:
            time.sleep(3)  # render settle
            break
    else:
        print(f"TIMEOUT: {out_path}"); ws.close(); return False
    # clip newest blob image
    v = js_eval(ws, '''(() => {
      const imgs = Array.from(document.querySelectorAll('img')).filter(i => i.src.startsWith('blob:') && i.naturalWidth > 300);
      const im = imgs[imgs.length - 1];
      const r = im.getBoundingClientRect();
      return JSON.stringify({x: r.x, y: r.y, w: r.width, h: r.height});
    })()''')
    d = json.loads(v)
    r = cdp("Page.captureScreenshot", {
        "format": "png",
        "clip": {"x": max(0, d['x'] - 4), "y": max(0, d['y'] - 4), "width": d['w'] + 8, "height": d['h'] + 8, "scale": 1}
    })
    with open(out_path, 'wb') as f:
        f.write(base64.b64decode(r['data']))
    print(f"SAVED {out_path}")
    ws.close()
    time.sleep(8)  # rate-limit spacing
    return True

jobs = [
    ("Professional product photograph: pair of black Muay Thai shin guards with red accent stitching standing upright on dark slate surface, studio side lighting, premium e-commerce product photography, sharp synthetic leather texture, minimalist dark background. No people, no text, no logos", "/home/ubuntu/ig_posts/AI_shinguards.png"),
    ("Professional product photograph: brown leather Thai pads (kickboxing pads) stacked, with focus mitts beside them, on dark slate surface, dramatic studio lighting, premium e-commerce style, visible leather grain, minimalist dark background. No people, no text, no logos", "/home/ubuntu/ig_posts/AI_thaipads.png"),
    ("Professional product photograph: black MMA fight shorts with subtle red waistband detail, neatly laid flat on dark slate surface, studio lighting, premium e-commerce product photography, sharp fabric texture, minimalist dark background. No people, no text, no logos", "/home/ubuntu/ig_posts/AI_mmashorts.png"),
    ("Professional product photograph: black long-sleeve compression rash guard with subtle red stitching, laid flat on dark slate surface, studio lighting, premium e-commerce style, sharp fabric texture, minimalist dark background. No people, no text, no logos", "/home/ubuntu/ig_posts/AI_rashguard.png"),
    ("Professional product photograph: white karate uniform gi with colored belts (yellow, orange, green, blue, brown, black) arranged in a fan beside it, on dark slate surface, studio lighting, premium e-commerce product photography, minimalist dark background. No people, no text, no logos", "/home/ubuntu/ig_posts/AI_karate.png"),
    ("Professional product photograph: navy blue judo gi uniform 750 GSM heavy weave, folded jacket with white belt on top, on dark slate surface, dramatic side studio lighting, premium e-commerce product photography, thick fabric texture visible, minimalist dark background. No people, no text, no logos", "/home/ubuntu/ig_posts/AI_judogi.png"),
    ("Professional product photograph: black boxing headgear with cheek protection standing on dark slate surface, studio side lighting, premium e-commerce product photography, premium leather texture, minimalist dark background. No people, no text, no logos", "/home/ubuntu/ig_posts/AI_headgear.png"),
    ("Professional product photograph: custom navy hoodie with small embroidered logo area on chest, neatly folded on dark slate surface, premium studio lighting, e-commerce product photography, sharp cotton fleece texture, minimalist dark background. No people, no text, no logos", "/home/ubuntu/ig_posts/AI_hoodie.png"),
]

for prompt, out in jobs:
    ok = gen(prompt, out)
    print(f"{'OK' if ok else 'FAIL'}: {out}")
