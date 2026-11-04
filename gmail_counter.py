#!/usr/bin/env python3
"""Day-20: reliable Gmail conversation counter.

The hash-URL approach silently FAILED (the query never applied - the page kept
showing the old result list). The working method is: type the query into the
real 'Search mail' input and press Enter, then read the '1-50 of N' header.
"""
import json
import re
import sys
import time

sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, make_cdp, js_eval


class GmailCounter:
    def __init__(self):
        tabs = get_tabs()
        gm = [t for t in tabs if 'mail.google' in t.get('url', '') and t.get('type') == 'page']
        if not gm:
            raise RuntimeError('NO GMAIL TAB')
        self.ws = connect(gm[0])
        self.cdp = make_cdp(self.ws)
        self.cdp('Page.enable')
        self.cdp('Page.bringToFront')
        time.sleep(1)

    def count(self, query, wait=8):
        js = """(()=>{
          const box=document.querySelector('input[aria-label="Search mail"]') ||
                    document.querySelector('input[name="q"]');
          if(!box) return 'no-box';
          box.focus();
          const setter=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
          setter.call(box,%s);
          box.dispatchEvent(new Event('input',{bubbles:true}));
          for (const type of ['keydown','keypress','keyup']) {
            box.dispatchEvent(new KeyboardEvent(type,{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}));
          }
          return 'typed';
        })()""" % json.dumps(query)
        r = js_eval(self.ws, js, await_promise=False)
        if r == 'no-box':
            raise RuntimeError('search box not found')
        time.sleep(wait)
        v = js_eval(self.ws, """(()=>{
          const m=document.querySelector('div[role="main"]');
          const t=m?m.innerText:'';
          const box=document.querySelector('input[aria-label="Search mail"]');
          const x=t.match(/([\\d,]+)\\s*[–-]\\s*[\\d,]+\\s+of\\s+([\\d,]+)/);
          const nomatch=/No messages matched your search/i.test(t);
          const many=/of many/i.test(t);
          return JSON.stringify({c:x?x[2]:null, nomatch:nomatch, many:many,
                                  box:box?box.value:'', head:t.slice(0,200).replace(/\\n/g,' | ')});})()""",
                       await_promise=False)
        try:
            return json.loads(v or '{}')
        except Exception:
            return {'c': None, 'raw': str(v)[:200]}

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


if __name__ == '__main__':
    g = GmailCounter()
    queries = [
        'in:sent after:2026/11/03',
        'in:sent after:2026/11/02',
        'in:sent newer_than:1d',
        'in:sent newer_than:2d',
        'in:sent newer_than:30d',
        'in:drafts newer_than:2d',
    ]
    for q in queries:
        r = g.count(q)
        print('%-34s -> c=%s nomatch=%s many=%s' % (q, r.get('c'), r.get('nomatch'), r.get('many')))
    g.close()
