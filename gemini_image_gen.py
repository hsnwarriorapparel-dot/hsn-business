#!/usr/bin/env python3
"""Generate product images via Gemini app (free Nano Banana mini) through the logged-in browser.
Usage: python3 gemini_image_gen.py "<prompt>" <output_path>"""
import sys, time, json, base64
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import *

def generate_image(prompt, out_path, wait_s=45):
    tabs = get_tabs()
    ais = [t for t in tabs if 'gemini.google' in t['url'] and t['type']=='page']
    if not ais:
        print("NO GEMINI TAB")
        return False
    ws = connect(ais[0])
    cdp = make_cdp(ws)
    cdp("Page.bringToFront")
    time.sleep(2)

    # find input + type
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

    # wait for generation
    for i in range(30):
        time.sleep(4)
        v = js_eval(ws, '''(() => {
          const img = Array.from(document.querySelectorAll('img')).find(i => i.src.startsWith('blob:') && i.naturalWidth > 300);
          const body = document.body.innerText;
          const creating = /creating your image/i.test(body.slice(-400));
          return JSON.stringify({hasImg: !!img, creating});
        })()''')
        try:
            d = json.loads(v)
        except Exception:
            continue
        if d.get('hasImg') and not d.get('creating'):
            break
    else:
        print("timeout waiting for image"); ws.close(); return False

    # clip-screenshot the image element
    v = js_eval(ws, '''(() => {
      const img = Array.from(document.querySelectorAll('img')).find(i => i.src.startsWith('blob:') && i.naturalWidth > 300);
      const r = img.getBoundingClientRect();
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
    # start a NEW chat for the next generation
    cdp("Page.navigate", {"url": "https://gemini.google.com/app"})
    time.sleep(6)
    ws.close()
    return True

if __name__ == '__main__':
    generate_image(sys.argv[1], sys.argv[2])
