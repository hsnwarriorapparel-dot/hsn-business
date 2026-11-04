#!/usr/bin/env python3
"""Day-20 debug 2: make the Gmail search actually apply, then read the count."""
import json
import sys
import time
import urllib.parse

sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

tabs = get_tabs()
gm = [t for t in tabs if 'mail.google' in t.get('url', '') and t.get('type') == 'page']
ws = connect(gm[0])
cdp = make_cdp(ws)
cdp('Page.enable')
cdp('Page.bringToFront')
time.sleep(1)


def read_state(label):
    v = js_eval(ws, """(()=>{
        const m=document.querySelector('div[role="main"]');
        const t=m?m.innerText:'';
        const box=document.querySelector('input[aria-label*="Search"], .aoR');
        const hdr=(document.querySelector('.gs .g3')||{}).innerText||'';
        return JSON.stringify({
          box: box?box.value:'',
          hdr: hdr.replace(/\\n/g,' | ').slice(0,160),
          head: t.slice(0,260).replace(/\\n/g,' | ')});})()""", await_promise=False)
    print('---', label)
    try:
        print('   ', json.loads(v or '{}'))
    except Exception:
        print('    raw:', str(v)[:300])


def set_search(q):
    """Type the query into the real search box and press Enter."""
    js = """(()=>{
        const box=document.querySelector('input[aria-label*="Search"], .aoR');
        if(!box) return 'no-box';
        box.focus();
        const setter=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
        setter.call(box, %s);
        box.dispatchEvent(new Event('input',{bubbles:true}));
        const f=box.form;
        if(f){f.submit(); return 'form-submit';}
        box.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}));
        return 'enter';
    })()""" % json.dumps(q)
    print('   set_search:', js_eval(ws, js, await_promise=False))


print('=== A. hash navigation ===')
cdp('Page.navigate', {'url': 'https://mail.google.com/mail/u/0/#search/' + urllib.parse.quote('in:sent after:2026/11/03')})
time.sleep(8)
read_state('after hash nav')

print('=== B. typing into the search box ===')
set_search('in:sent after:2026/11/03')
time.sleep(9)
read_state('after typed search')

print('=== C. control: newer_than:2d ===')
set_search('in:sent newer_than:2d')
time.sleep(9)
read_state('after newer_than:2d')

print('=== D. control: subject variant ===')
set_search('in:sent newer_than:1d subject:"custom club apparel"')
time.sleep(9)
read_state('after subject variant')

ws.close()
