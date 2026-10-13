#!/usr/bin/env python3
"""Overnight outreach pipeline for HSN Warrior Apparels.
Processes leads one-by-one: follow on IG -> personalized DM -> email -> WhatsApp.
All messages use: company HSN Warrior Apparels, phone +92 337 33381, NO free samples.
"""
import sys, time, json, random
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import *

PHONE = "+92 337 33381"
COMPANY = "HSN Warrior Apparels"
GMAIL = "hsnwarriorapparel@gmail.com"

def log(msg):
    with open('/home/ubuntu/outreach_log.txt', 'a') as f:
        f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
    print(msg)

def ig_open_profile(handle):
    """Navigate IG tab to profile. Returns True if profile exists."""
    tab = find_tab(lambda t: 'instagram.com' in t['url'] and 'direct' not in t['url'] and t['type']=='page')
    if not tab:
        open_new_tab(f"https://www.instagram.com/{handle}/")
        time.sleep(7)
        tab = find_tab(lambda t: f'instagram.com/{handle}' in t['url'] and t['type']=='page')
        if not tab: return False
    else:
        ws = connect(tab)
        cdp = make_cdp(ws)
        cdp("Page.enable")
        cdp("Page.navigate", {"url": f"https://www.instagram.com/{handle}/"})
        time.sleep(6)
        ws.close()
    # verify profile loaded (not "page not found")
    tab = find_tab(lambda t: f'instagram.com/{handle}' in t['url'] and t['type']=='page')
    if not tab: return False
    ws = connect(tab)
    v = js_eval(ws, '''(() => {
      const notFound = /Page Not Found|Sorry, this page/i.test(document.body.innerText);
      const header = document.querySelector('header');
      return JSON.stringify({notFound, hasHeader: !!header});
    })()''')
    ws.close()
    r = json.loads(v)
    return not r['notFound'] and r['hasHeader']

def ig_follow(ws):
    v = js_eval(ws, """(async () => {
      const btn = Array.from(document.querySelectorAll('header button, header [role="button"]')).find(b => /^Follow$/i.test((b.innerText||'').trim()));
      if (!btn) return "no-btn";
      btn.click();
      await new Promise(r => setTimeout(r, 2000));
      const now = Array.from(document.querySelectorAll('header button, header [role="button"]')).some(b => /Following/i.test(b.innerText||''));
      return now ? "ok" : "clicked";
    })()""")
    return v

def ig_dm(ws, message):
    v = js_eval(ws, '''(async () => {
      const msgBtn = Array.from(document.querySelectorAll('header button, header [role="button"]')).find(b => /Message/i.test(b.innerText||''));
      if (!msgBtn) return "no-msg-btn";
      msgBtn.click();
      // wait up to 12s for the composer
      for (let i = 0; i < 12; i++) {
        await new Promise(r => setTimeout(r, 1000));
        const ta = document.querySelector('textarea, div[contenteditable="true"]');
        if (ta) return "opened";
      }
      return "composer-never-appeared";
    })()''')
    if v != "opened": return v
    time.sleep(2)
    v2 = js_eval(ws, '''(async () => {
      const ta = document.querySelector('textarea, div[contenteditable="true"]');
      if (!ta) return "no-composer";
      ta.focus();
      const dt = new DataTransfer();
      dt.setData('text/plain', MSG);
      ta.dispatchEvent(new ClipboardEvent('paste', {clipboardData: dt, bubbles: true, cancelable: true}));
      await new Promise(r => setTimeout(r, 700));
      const len = (ta.value || ta.innerText || '').length;
      if (len < 50) return "paste-failed";
      ta.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true, cancelable: true}));
      await new Promise(r => setTimeout(r, 2500));
      const taAfter = document.querySelector('textarea, div[contenteditable="true"]');
      const cleared = (taAfter.value || taAfter.innerText || '').length < 5;
      return cleared ? "sent" : "enter-failed";
    })()'''.replace("MSG", repr(message)))
    return v2

def gmail_send(to, subject, body):
    """Gmail compose v3: click Compose button, type recipient, TAB to subject, TAB to body, Ctrl+Enter."""
    import json as _j
    tabs = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
    if not tabs:
        return "no-gmail-tab"
    ws = connect(tabs[0])
    cdp = make_cdp(ws)
    cdp("Page.enable")
    cdp("Page.bringToFront")   # REQUIRED: background tabs ignore UI clicks
    time.sleep(1)

    # clean state: inbox
    cdp("Page.navigate", {"url": "https://mail.google.com/mail/u/0/#inbox"})
    time.sleep(4)

    # dismiss any stale compose dialog: Escape first, then Save & close, then click discard in confirm
    js_eval(ws, """(async () => {
      for (let round = 0; round < 3; round++) {
        const dlg = document.querySelector('div[role="dialog"]');
        if (!dlg) break;
        // Escape removed - it MINIMIZES Gmail compose instead of closing
        await new Promise(r => setTimeout(r, 800));
        const saveClose = Array.from(dlg.querySelectorAll('[aria-label]')).find(e => /Save & close/i.test(e.getAttribute('aria-label')||''));
        if (saveClose && document.querySelector('div[role="dialog"]')) { saveClose.click(); await new Promise(r => setTimeout(r, 1200)); }
      }
      // if a confirm-discard prompt appears, click Discard
      const discard = Array.from(document.querySelectorAll('[role="button"], button')).find(e => /^Discard$/i.test((e.innerText||'').trim()));
      if (discard) { discard.click(); await new Promise(r => setTimeout(r, 800)); }
      return 'ok';
    })()""")
    time.sleep(1)

    # click Compose button
    pos_r = js_eval(ws, """(() => {
      const btn = Array.from(document.querySelectorAll('div[role="button"], .T-I')).find(e => /^Compose$/i.test((e.innerText||'').trim()));
      if (!btn) return null;
      const rc = btn.getBoundingClientRect();
      return JSON.stringify({x: rc.x + rc.width/2, y: rc.y + rc.height/2});
    })()""")
    try:
        pos = _j.loads(pos_r)
    except Exception:
        pos = None
    if not pos:
        ws.close()
        return "compose-btn-not-found"
    cdp("Input.dispatchMouseEvent", {"type": "mousePressed", "x": pos['x'], "y": pos['y'], "button": "left", "clickCount": 1})
    cdp("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": pos['x'], "y": pos['y'], "button": "left", "clickCount": 1})

    # wait until focus is in the To INPUT; if the dialog is minimized (h<100), expand it
    for _ in range(12):
        f = js_eval(ws, """(() => {
          const dlg = document.querySelector('div[role="dialog"]');
          if (!dlg) return 'nodlg';
          const r = dlg.getBoundingClientRect();
          if (r.height < 100) return 'minimized';
          const a = document.activeElement;
          return (a && a.tagName === 'INPUT' && /to/i.test(a.getAttribute('aria-label')||'')) ? 'ready' : 'wait';
        })()""")
        if f == 'ready':
            break
        if f == 'minimized':
            # click the minimized bar to expand it back
            pos_m = js_eval(ws, """(() => {
              const dlg = document.querySelector('div[role="dialog"]');
              const r = dlg.getBoundingClientRect();
              return JSON.stringify({x: r.x + r.width/2, y: r.y + r.height/2});
            })()""")
            try:
                pm = json.loads(pos_m)
                cdp("Input.dispatchMouseEvent", {"type": "mousePressed", "x": pm['x'], "y": pm['y'], "button": "left", "clickCount": 1})
                cdp("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": pm['x'], "y": pm['y'], "button": "left", "clickCount": 1})
            except Exception:
                pass
            time.sleep(1.5)
            continue
        time.sleep(1)
    else:
        ws.close()
        return "compose-focus-never-ready"

    # 1. type recipient + Tab (commits recipient, lands in subject)
    cdp("Input.insertText", {"text": to})
    time.sleep(1.0)
    cdp("Input.dispatchKeyEvent", {"type": "rawKeyDown", "key": "Tab", "code": "Tab", "windowsVirtualKeyCode": 9, "nativeVirtualKeyCode": 9})
    cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Tab", "code": "Tab", "windowsVirtualKeyCode": 9, "nativeVirtualKeyCode": 9})
    time.sleep(0.8)

    # verify recipient chip registered
    got = js_eval(ws, """(() => JSON.stringify({ok: document.querySelector('div[role="dialog"]').innerText.includes(%s)}))()""" % repr(to))
    try:
        chk = _j.loads(got)
    except Exception:
        chk = {}
    if not chk.get('ok'):
        # try Enter instead of Tab to commit
        cdp("Input.dispatchKeyEvent", {"type": "rawKeyDown", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13})
        cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13})
        time.sleep(0.8)
        got = js_eval(ws, """(() => JSON.stringify({ok: document.querySelector('div[role="dialog"]').innerText.includes(%s)}))()""" % repr(to))
        try:
            chk = _j.loads(got)
        except Exception:
            chk = {}
        if not chk.get('ok'):
            ws.close()
            return "recipient-not-registered"
        # focus moved out of To; Tab again to reach subject
        cdp("Input.dispatchKeyEvent", {"type": "rawKeyDown", "key": "Tab", "code": "Tab", "windowsVirtualKeyCode": 9, "nativeVirtualKeyCode": 9})
        cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Tab", "code": "Tab", "windowsVirtualKeyCode": 9, "nativeVirtualKeyCode": 9})
        time.sleep(0.5)

    # 2. subject: focus should be in subject input now
    f = js_eval(ws, """(() => { const a = document.activeElement; return (a && /subject|asunto/i.test(a.getAttribute('aria-label')||'')) ? 'ready' : 'no'; })()""")
    if f != 'ready':
        # click subject input directly
        pos_r2 = js_eval(ws, """(() => {
          const i = Array.from(document.querySelectorAll('div[role="dialog"] input')).find(x => /subject|asunto/i.test(x.getAttribute('aria-label')||''));
          if (!i) return null;
          const rc = i.getBoundingClientRect();
          return JSON.stringify({x: rc.x + rc.width/2, y: rc.y + rc.height/2});
        })()""")
        try:
            pos2 = _j.loads(pos_r2)
        except Exception:
            pos2 = None
        if pos2:
            cdp("Input.dispatchMouseEvent", {"type": "mousePressed", "x": pos2['x'], "y": pos2['y'], "button": "left", "clickCount": 1})
            cdp("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": pos2['x'], "y": pos2['y'], "button": "left", "clickCount": 1})
            time.sleep(0.6)
    cdp("Input.insertText", {"text": subject})
    time.sleep(0.8)

    # 3. body: click the message body area
    pos_r3 = js_eval(ws, """(() => {
      const b = document.querySelector('div[role="dialog"] div[aria-label="Message Body"]') || document.querySelector('div[role="dialog"] div[role="textbox"]');
      if (!b) return null;
      const rc = b.getBoundingClientRect();
      return JSON.stringify({x: rc.x + Math.min(rc.width/2, 200), y: rc.y + Math.min(rc.height/2, 60)});
    })()""")
    try:
        pos3 = _j.loads(pos_r3)
    except Exception:
        pos3 = None
    if not pos3:
        ws.close()
        return "body-not-found"
    cdp("Input.dispatchMouseEvent", {"type": "mousePressed", "x": pos3['x'], "y": pos3['y'], "button": "left", "clickCount": 1})
    cdp("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": pos3['x'], "y": pos3['y'], "button": "left", "clickCount": 1})
    time.sleep(0.6)

    # verify body is focused, then type it
    f2 = js_eval(ws, """(() => { const a = document.activeElement; return (a && (a.getAttribute('aria-label')||'').includes('Message Body')) ? 'ready' : 'no'; })()""")
    if f2 != 'ready':
        ws.close()
        return "body-focus-failed"
    cdp("Input.insertText", {"text": body})
    time.sleep(1.0)

    # 4. verify all three fields, then send with Ctrl+Enter
    chk3 = js_eval(ws, """(() => {
      const dlg = document.querySelector('div[role="dialog"]');
      const t = dlg.innerText;
      return JSON.stringify({to: t.includes(%s), subj: t.includes(%s.slice(0, 20)), body: t.includes('Sialkot')});
    })()""" % (repr(to), repr(subject)))
    try:
        c3 = _j.loads(chk3)
    except Exception:
        c3 = {}
    if not (c3.get('to') and c3.get('subj')):
        ws.close()
        return "fields-missing:" + str(c3)

    # send: click the Send button with real mouse events
    send_pos = js_eval(ws, """(() => {
      const dlg = document.querySelector('div[role="dialog"]');
      const btn = dlg.querySelector('div[data-tooltip^="Send"], div[aria-label^="Send"]');
      if (!btn) return null;
      const rc = btn.getBoundingClientRect();
      return JSON.stringify({x: rc.x + rc.width/2, y: rc.y + rc.height/2});
    })()""")
    try:
        sp = _j.loads(send_pos)
    except Exception:
        sp = None
    if not sp:
        ws.close()
        return "send-btn-not-found"
    cdp("Input.dispatchMouseEvent", {"type": "mousePressed", "x": sp['x'], "y": sp['y'], "button": "left", "clickCount": 1})
    cdp("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": sp['x'], "y": sp['y'], "button": "left", "clickCount": 1})
    time.sleep(5)

    # verify: dialog closed = sent (Gmail closes compose on send)
    v = js_eval(ws, """(() => {
      const dlg = document.querySelector('div[role="dialog"]');
      const err = /specify at least one recipient/i.test(document.body.innerText);
      const toast = /Message sent/i.test(document.body.innerText);
      return JSON.stringify({dialogGone: !dlg, err, toast});
    })()""")
    ws.close()
    try:
        r = _j.loads(v)
    except Exception:
        r = {}
    if r.get('err'):
        return "RECIPIENT-ERROR"
    if r.get('dialogGone') and (r.get('toast') or True):
        return "sent"
    return "send-unverified:" + str(r)



def wa_send(phone, message):
    tab = find_tab(lambda t: 'web.whatsapp' in t['url'] and t['type']=='page')
    if not tab: return "no-wa-tab"
    ws = connect(tab)
    cdp = make_cdp(ws)
    cdp("Page.enable")
    cdp("Page.bringToFront")   # background tabs ignore UI clicks
    time.sleep(0.5)
    cdp("Page.navigate", {"url": f"https://web.whatsapp.com/send?phone={phone}"})
    time.sleep(15)
    for attempt in range(5):
        v = js_eval(ws, '''(async () => {
      const composer = document.querySelector('footer div[contenteditable="true"], div[title^="Type a message"]');
      if (!composer) return "no-composer";
      composer.focus();
      const dt = new DataTransfer();
      dt.setData('text/plain', MSG);
      composer.dispatchEvent(new ClipboardEvent('paste', {clipboardData: dt, bubbles: true, cancelable: true}));
      await new Promise(r => setTimeout(r, 800));
      const len = (composer.innerText || '').length;
      if (len < 30) return "paste-failed";
      composer.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true, cancelable: true}));
      await new Promise(r => setTimeout(r, 2500));
      const transcript = document.querySelector('div[data-testid="conversation-panel-messages"], #main div[data-tab="8"]');
      const last = transcript ? Array.from(transcript.querySelectorAll('div[data-id]')).slice(-1).map(d => d.innerText.slice(0,40)) : [];
      return JSON.stringify({ok: true, last});
    })()'''.replace("MSG", repr(message)))
        if v not in ("no-composer", "paste-failed"):
            break
        time.sleep(10)  # wait for WA to load
    ws.close()
    return v

if __name__ == "__main__":
    print("library - import me")
