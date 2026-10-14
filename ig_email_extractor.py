#!/usr/bin/env python3
"""Extract emails + WA numbers from Instagram business profiles.
Opens profile -> checks bio -> clicks Contact button -> reads email/phone.
For Day 4: leads found via IG get their email hunted from their own profile."""
import sys, time, json, re
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import *
from outreach import ig_open_profile

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
PHONE_RE = re.compile(r'\+?[0-9][0-9 ]{8,16}[0-9]')

def extract_from_profile(handle):
    """Returns {'email': str|None, 'phone': str|None, 'bio': str}"""
    handle = handle.lstrip('@')
    ok = ig_open_profile(handle)
    if not ok:
        return None
    tabs = get_tabs()
    tab = [t for t in tabs if f'instagram.com/{handle}' in t['url'] and t['type'] == 'page']
    if not tab:
        return None
    ws = connect(tab[-1])
    try:
        time.sleep(3)
        # 1. read bio text (header section)
        v = js_eval(ws, '''(() => {
          const header = document.querySelector('header');
          return header ? header.innerText : '';
        })()''')
        bio = v if v else ''
        # expand truncated bio if possible
        if 'more' in bio.lower():
            js_eval(ws, """(async () => {
              const more = Array.from(document.querySelectorAll('header span, header div')).find(e => (e.innerText||'').trim().toLowerCase() === 'more');
              if (more) { more.click(); await new Promise(r => setTimeout(r, 800)); }
              return true;
            })()""")
            v3 = js_eval(ws, "(() => document.querySelector('header').innerText)()")
            if v3: bio = v3
        email = None; phone = None
        em = EMAIL_RE.search(bio)
        if em: email = em.group(0)
        ph = PHONE_RE.search(bio)
        if ph: phone = ph.group(0).replace(' ', '')
        # 2. if no email in bio, click Contact button if present
        if not email:
            v2 = js_eval(ws, '''(async () => {
              const btn = Array.from(document.querySelectorAll('button, a[role="button"], div[role="button"]'))
                .find(b => (b.innerText || '').trim().toLowerCase() === 'contact');
              if (!btn) return null;
              btn.click();
              await new Promise(r => setTimeout(r, 1500));
              const dialog = document.querySelector('div[role="dialog"]');
              return dialog ? dialog.innerText : null;
            })()''')
            if v2:
                em = EMAIL_RE.search(v2)
                if em: email = em.group(0)
                ph = PHONE_RE.search(v2)
                if ph: phone = ph.group(0).replace(' ', '')
                # close dialog
                js_eval(ws, '''(async () => {
                  const close = document.querySelector('div[role="dialog"] svg[aria-label="Close"], div[role="dialog"] [aria-label="Close"]');
                  if (close) close.closest('button') ? close.closest('button').click() : close.click();
                  await new Promise(r => setTimeout(r, 800));
                  return true;
                })()''')
        # 3. last resort: their website link -> scrape for email (wa.me too)
        if not email:
            v4 = js_eval(ws, """(async () => {
              const links = Array.from(document.querySelectorAll('header a[href]')).map(a => a.href).filter(h => !h.includes('instagram.com'));
              return links.length ? links[0] : null;
            })()""")
            if v4:
                import subprocess
                try:
                    r = subprocess.run(['curl', '-sL', '--max-time', '8', v4], capture_output=True, text=True, timeout=12)
                    html = r.stdout or ''
                    em = EMAIL_RE.search(html)
                    if em: email = em.group(0)
                    if not phone:
                        import re as _re
                        wm = _re.search(r'wa\.me/([0-9]{8,15})', html)
                        if wm: phone = wm.group(1)
                except Exception:
                    pass
        return {'email': email, 'phone': phone, 'bio': bio[:200]}
    finally:
        ws.close()

if __name__ == '__main__':
    # test mode: extract from a known gym profile
    test = sys.argv[1] if len(sys.argv) > 1 else 'moralesbox'
    print(extract_from_profile(test))
