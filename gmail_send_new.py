def gmail_send(to, subject, body):
    """Gmail compose via CDP real-input pipeline (Input.insertText + real clicks).
    Returns 'sent' / 'RECIPIENT-ERROR' / reason string."""
    import json as _j
    tabs = [t for t in get_tabs() if 'mail.google' in t['url'] and t['type'] == 'page']
    if not tabs:
        return "no-gmail-tab"
    ws = connect(tabs[0])
    cdp = make_cdp(ws)
    cdp("Page.enable")
    cdp("Page.navigate", {"url": "https://mail.google.com/mail/u/0/#inbox?compose=new"})
    time.sleep(5)

    # wait for compose dialog
    for _ in range(10):
        if js_eval(ws, '(() => !!document.querySelector(\'div[role="dialog"]\'))()'):
            break
        time.sleep(1)
    else:
        ws.close()
        return "compose-never-opened"

    def click_el(finder_js):
        r = js_eval(ws, """(async () => {
          const el = %s;
          if (!el) return "null";
          const rc = el.getBoundingClientRect();
          return JSON.stringify({x: rc.x + rc.width/2, y: rc.y + rc.height/2});
        })()""" % finder_js)
        try:
            pos = _j.loads(r)
        except Exception:
            return None
        if not pos or 'x' not in pos:
            return None
        cdp("Input.dispatchMouseEvent", {"type": "mousePressed", "x": pos['x'], "y": pos['y'], "button": "left", "clickCount": 1})
        cdp("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": pos['x'], "y": pos['y'], "button": "left", "clickCount": 1})
        return True

    # 1. To field
    if not click_el("document.querySelector('div[role=\"dialog\"] input')"):
        ws.close()
        return "to-click-failed"
    time.sleep(0.5)
    cdp("Input.insertText", {"text": to})
    time.sleep(1.2)
    cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Tab", "code": "Tab", "windowsVirtualKeyCode": 9, "nativeVirtualKeyCode": 9})
    cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Tab", "code": "Tab", "windowsVirtualKeyCode": 9, "nativeVirtualKeyCode": 9})
    time.sleep(0.6)

    # verify recipient registered
    got = js_eval(ws, """(() => JSON.stringify({ok: document.querySelector('div[role="dialog"]').innerText.includes(%s)}))()""" % repr(to))
    try:
        chk = _j.loads(got)
    except Exception:
        chk = {}
    if not chk.get('ok'):
        cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13})
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

    # 2. Subject
    if not click_el("Array.from(document.querySelector('div[role=\"dialog\"]').querySelectorAll('input')).find(i => /subject|asunto/i.test(i.getAttribute('aria-label')||''))"):
        ws.close()
        return "subject-click-failed"
    time.sleep(0.4)
    cdp("Input.insertText", {"text": subject})
    time.sleep(0.5)

    # 3. Body
    if not click_el("document.querySelector('div[role=\"dialog\"] div[aria-label=\"Message Body\"], div[role=\"dialog\"] div[role=\"textbox\"]')"):
        ws.close()
        return "body-click-failed"
    time.sleep(0.4)
    cdp("Input.insertText", {"text": body})
    time.sleep(0.8)

    # 4. Send via Ctrl+Enter
    cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13, "modifiers": 2})
    cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13})
    time.sleep(4)

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
    if r.get('dialogGone') or r.get('toast'):
        return "sent"
    return "send-unverified"
