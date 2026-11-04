#!/usr/bin/env python3
"""Day-20 debug 3: enumerate Gmail search inputs + try a full-document reload."""
import json
import sys
import time
import urllib.parse

sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval

tabs = get_tabs()
gm = [t for t in tabs if 'mail.google' in t.get('url', '') and t.get('type') == 'page']
print('gmail tab url:', gm[0]['url'])
ws = connect(gm[0])
cdp = make_cdp(ws)
cdp('Page.enable')
cdp('Page.bringToFront')
time.sleep(1)

print('=== inputs on page ===')
v = js_eval(ws, """(()=>{
  const out=[];
  document.querySelectorAll('input,textarea').forEach((e,i)=>{
    out.push({i:i, tag:e.tagName, type:e.type||'', name:e.name||'', aria:e.getAttribute('aria-label')||'',
              val:(e.value||'').slice(0,80), vis:!!(e.offsetWidth||e.offsetHeight)});
  });
  return JSON.stringify(out);})()""", await_promise=False)
try:
    for it in json.loads(v or '[]'):
        print('  ', it)
except Exception:
    print('  raw:', str(v)[:400])

print('=== forced document reload with query ===')
url = ('https://mail.google.com/mail/u/0/?shva=1#search/'
       + urllib.parse.quote('in:sent after:2026/11/03'))
cdp('Page.navigate', {'url': url})
time.sleep(4)
cdp('Page.reload', {'ignoreCache': False})
time.sleep(10)
v = js_eval(ws, """(()=>{
  const m=document.querySelector('div[role="main"]');
  const t=m?m.innerText:'';
  const box=document.querySelector('input[aria-label*="Search"]');
  return JSON.stringify({box: box?box.value:'', head:t.slice(0,500).replace(/\\n/g,' | ')});})()""",
               await_promise=False)
print('  ', v)

print('=== retry: type into the main search input ===')
js = """(()=>{
  const box=document.querySelector('input[aria-label*="Search"]');
  if(!box) return 'no-box';
  box.focus();
  const setter=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
  setter.call(box,'in:sent after:2026/11/03');
  box.dispatchEvent(new Event('input',{bubbles:true}));
  box.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}));
  box.dispatchEvent(new KeyboardEvent('keypress',{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}));
  box.dispatchEvent(new KeyboardEvent('keyup',{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}));
  return 'typed';
})()"""
print('  ', js_eval(ws, js, await_promise=False))
time.sleep(10)
v = js_eval(ws, """(()=>{
  const m=document.querySelector('div[role="main"]');
  const t=m?m.innerText:'';
  const box=document.querySelector('input[aria-label*="Search"]');
  const x=t.match(/([\\d,]+)\\s*[–-]\\s*[\\d,]+\\s+of\\s+([\\d,]+)/);
  return JSON.stringify({box: box?box.value:'', c:x?x[2]:null, head:t.slice(0,400).replace(/\\n/g,' | ')});})()""",
               await_promise=False)
print('  ', v)
ws.close()
