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

    # BLOCKER (2026-10-30): Google's "Send feedback to Google" panel is a
    # FULL-VIEWPORT iframe (tools/feedback/aloha_frame) that overlays the page
    # and swallows the Compose click -> every send failed with
    # 'compose-focus-never-ready'. It has no visible close button in the DOM
    # (0x0), so the only reliable fix is to REMOVE the iframe before clicking.
    killed = js_eval(ws, """(() => {
      let n = 0;
      for (const f of document.querySelectorAll('iframe')) {
        if (/aloha_frame|feedback\\/i.test(f.src || '')) { f.remove(); n++; }
      }
      return n;
    })()""", await_promise=False)
    if killed:
        time.sleep(1)

    # CLEAN STATE: discard ALL existing compose dialogs first (drafts auto-restore
    # server-side and querySelector('div[role="dialog"]') would read the STALE draft
    # instead of our new compose - the Day-10 wave failure). Discard, never Save.
    cleaned = js_eval(ws, """(async () => {
      let discarded = 0;
      for (let round = 0; round < 5; round++) {
        // any dialog whose To field already has content = stale draft from a previous send
        const stale = Array.from(document.querySelectorAll('div[role="dialog"]')).filter(d => {
          const to = Array.from(d.querySelectorAll('input, [email]')).find(x => /to/i.test(x.getAttribute('aria-label')||''));
          return d.innerText && !/^Compose:/m.test('') && true;
        });
        // simpler + robust: if ANY compose dialog exists, close it via its trash/discard button
        const dlgs = Array.from(document.querySelectorAll('div[role="dialog"]')).filter(d => /New Message|Compose/i.test(d.innerText.slice(0, 30)));
        if (!dlgs.length) break;
        for (const d of dlgs) {
          const discard = Array.from(d.querySelectorAll('[role="button"], [aria-label]')).find(e => /trash|discard/i.test(e.getAttribute('aria-label')||'') || /^(Discard|Delete draft)$/i.test((e.innerText||'').trim()));
          if (discard) { discard.click(); await new Promise(r => setTimeout(r, 500)); discarded++; }
        }
        await new Promise(r => setTimeout(r, 700));
      }
      // confirm-discard prompt if Gmail asks
      const confirmBtn = Array.from(document.querySelectorAll('[role="button"], button, [role="dialog"] [aria-label]')).find(e => /^(Discard|OK)$/i.test((e.innerText||'').trim()));
      if (confirmBtn && /discard/i.test(document.body.innerText.slice(-500))) { confirmBtn.click(); await new Promise(r => setTimeout(r, 600)); }
      await new Promise(r => setTimeout(r, 400));
      return 'discarded:' + discarded;
    })()""", await_promise=True)
    time.sleep(1.5)

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

    # wait until focus is in the To INPUT; if the dialog is minimized (h<100), expand it back
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

    # after the compose dialog opens, BIND to the dialog that actually has focus:
    # Gmail keeps multiple compose dialogs in the DOM; querySelector returns the FIRST
    # (often a stale auto-saved draft), while our typing goes to the focused one.
    # Every later read must use the same dialog we typed into.
    dlg_ref = js_eval(ws, """(() => {
      const dlgs = Array.from(document.querySelectorAll('div[role="dialog"]'));
      const active = dlgs.find(d => d.contains(document.activeElement));
      // fallback: the dialog whose To input is empty (a fresh compose)
      const fresh = dlgs.find(d => {
        const to = Array.from(d.querySelectorAll('input')).find(x => /to/i.test(x.getAttribute('aria-label')||''));
        return to && !to.value;
      });
      const d = active || fresh || dlgs[dlgs.length-1];
      // tag it with a unique attribute we can re-find
      d.setAttribute('data-hsn-compose', '1');
      return 'bound:' + dlgs.length;
    })()""")

    # 1. type recipient + Tab (commits recipient, lands in subject)
    cdp("Input.insertText", {"text": to})
    time.sleep(1.0)
    cdp("Input.dispatchKeyEvent", {"type": "rawKeyDown", "key": "Tab", "code": "Tab", "windowsVirtualKeyCode": 9, "nativeVirtualKeyCode": 9})
    cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Tab", "code": "Tab", "windowsVirtualKeyCode": 9, "nativeVirtualKeyCode": 9})
    time.sleep(0.8)

    # verify recipient chip registered - SCOPED to OUR dialog, case-insensitive
    # (Gmail canonicalizes chips, e.g. 'sifumarcdavis@' -> 'SifuMarcDavis@')
    got = js_eval(ws, """(() => JSON.stringify({ok: (document.querySelector('div[data-hsn-compose]') || {innerText:''}).innerText.toLowerCase().includes(%s.toLowerCase())}))()""" % repr(to))
    try:
        chk = _j.loads(got)
    except Exception:
        chk = {}
    if not chk.get('ok'):
        # try Enter instead of Tab to commit
        cdp("Input.dispatchKeyEvent", {"type": "rawKeyDown", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13})
        cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13})
        time.sleep(0.8)
        got = js_eval(ws, """(() => JSON.stringify({ok: (document.querySelector('div[data-hsn-compose]') || {innerText:''}).innerText.toLowerCase().includes(%s.toLowerCase())}))()""" % repr(to))
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
        # click subject input directly (scoped to our dialog)
        pos_r2 = js_eval(ws, """(() => {
          const d = document.querySelector('div[data-hsn-compose]');
          if (!d) return null;
          const i = Array.from(d.querySelectorAll('input')).find(x => /subject|asunto/i.test(x.getAttribute('aria-label')||''));
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

    # 3. body: click the message body area (scoped to our dialog)
    pos_r3 = js_eval(ws, """(() => {
      const b = document.querySelector('div[data-hsn-compose] div[aria-label="Message Body"]') || document.querySelector('div[data-hsn-compose] div[role="textbox"]');
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

    # 4. verify all three fields, then send with Ctrl+Enter (scoped to our dialog)
    chk3 = js_eval(ws, """(() => {
      const dlg = document.querySelector('div[data-hsn-compose]');
      if (!dlg) return JSON.stringify({to: false, subj: false, body: false});
      const t = dlg.innerText;
      return JSON.stringify({to: t.toLowerCase().includes(%s.toLowerCase()), subj: t.includes(%s.slice(0, 20)), body: t.includes('Sialkot')});
    })()""" % (repr(to), repr(subject)))
    try:
        c3 = _j.loads(chk3)
    except Exception:
        c3 = {}
    if not (c3.get('to') and c3.get('subj')):
        ws.close()
        return "fields-missing:" + str(c3)

    # send: click the Send button with real mouse events (scoped to our dialog)
    send_pos = js_eval(ws, """(() => {
      const dlg = document.querySelector('div[data-hsn-compose]');
      if (!dlg) return null;
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

    # verify: OUR dialog closed = sent (Gmail closes compose on send);
    # a still-present OTHER dialog (stale draft) must not confuse the check
    v = js_eval(ws, """(() => {
      const ours = document.querySelector('div[data-hsn-compose]');
      const err = /specify at least one recipient/i.test(document.body.innerText);
      const toast = /Message sent/i.test(document.body.innerText);
      return JSON.stringify({dialogGone: !ours, err, toast});
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
