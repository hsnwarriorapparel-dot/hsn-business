"""Send an email with a file attachment through Gmail (CDP).

Gmail's attach button opens a native file picker, which a browser cannot
drive directly. But Gmail ALSO exposes a hidden <input type="file"> in the
compose dialog once you click the attach button - and CDP's
DOM.setFileInputFiles can set that input directly, which bypasses the OS
file dialog entirely.

Usage:
    python3 gmail_send_attach.py <to> <subject> <body_file> <attach_path> [<attach_path> ...]
"""
import json
import os
import sys
import time

sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval, make_cdp


def send_with_attachment(to, subject, body, files):
    tabs = get_tabs()
    gm = [t for t in tabs if 'mail.google' in t.get('url', '') and t.get('type') == 'page']
    if not gm:
        return 'no-gmail-tab'
    ws = connect(gm[0])
    cdp = make_cdp(ws)
    cdp('Page.enable')
    cdp('DOM.enable')
    cdp('Page.navigate', {'url': 'https://mail.google.com/mail/u/0/#inbox?compose=new'})
    time.sleep(6)

    # wait for the compose dialog
    for _ in range(12):
        if js_eval(ws, '(() => !!document.querySelector(\'div[role="dialog"]\'))()'):
            break
        time.sleep(1)
    else:
        ws.close()
        return 'compose-never-opened'

    def click_el(finder_js):
        r = js_eval(ws, """(async () => {
          const el = %s;
          if (!el) return "null";
          const rc = el.getBoundingClientRect();
          return JSON.stringify({x: rc.x + rc.width/2, y: rc.y + rc.height/2});
        })()""" % finder_js)
        try:
            pos = json.loads(r)
        except Exception:
            return None
        if not pos or 'x' not in pos:
            return None
        cdp('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': pos['x'],
                                         'y': pos['y'], 'button': 'left', 'clickCount': 1})
        cdp('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': pos['x'],
                                         'y': pos['y'], 'button': 'left', 'clickCount': 1})
        return True

    # ---- To field ----
    if not click_el("document.querySelector('div[role=\"dialog\"] input')"):
        ws.close()
        return 'to-click-failed'
    time.sleep(0.5)
    cdp('Input.insertText', {'text': to})
    time.sleep(1.2)
    for typ in ('keyDown', 'keyUp'):
        cdp('Input.dispatchKeyEvent', {'type': typ, 'key': 'Tab', 'code': 'Tab',
                                       'windowsVirtualKeyCode': 9, 'nativeVirtualKeyCode': 9})
    time.sleep(0.8)

    got = js_eval(ws, """(() => JSON.stringify({ok: document.querySelector('div[role="dialog"]').innerText.includes(%s)}))()""" % repr(to))
    try:
        chk = json.loads(got)
    except Exception:
        chk = {}
    if not chk.get('ok'):
        for typ in ('keyDown', 'keyUp'):
            cdp('Input.dispatchKeyEvent', {'type': typ, 'key': 'Enter', 'code': 'Enter',
                                           'windowsVirtualKeyCode': 13, 'nativeVirtualKeyCode': 13})
        time.sleep(1.0)
        got = js_eval(ws, """(() => JSON.stringify({ok: document.querySelector('div[role="dialog"]').innerText.includes(%s)}))()""" % repr(to))
        try:
            chk = json.loads(got)
        except Exception:
            chk = {}
        if not chk.get('ok'):
            ws.close()
            return 'recipient-not-registered'

    # ---- Subject ----
    if not click_el("Array.from(document.querySelector('div[role=\"dialog\"]').querySelectorAll('input')).find(i => /subject|asunto/i.test(i.getAttribute('aria-label')||''))"):
        ws.close()
        return 'subject-click-failed'
    time.sleep(0.4)
    cdp('Input.insertText', {'text': subject})
    time.sleep(0.5)

    # ---- Body ----
    if not click_el("document.querySelector('div[role=\"dialog\"] div[aria-label=\"Message Body\"], div[role=\"dialog\"] div[role=\"textbox\"]')"):
        ws.close()
        return 'body-click-failed'
    time.sleep(0.4)
    cdp('Input.insertText', {'text': body})
    time.sleep(0.8)

    # ---- Attachment ----
    attached = []
    for f in files:
        # find the hidden file input in the compose dialog
        node = js_eval(ws, """(() => {
          const dlg = document.querySelector('div[role="dialog"]');
          if (!dlg) return 'no-dialog';
          const inp = dlg.querySelector('input[type="file"]');
          if (!inp) return 'no-file-input';
          return 'ok';
        })()""")
        if node != 'ok':
            # clicking the attach button reveals the file input
            click_el("Array.from(document.querySelector('div[role=\"dialog\"]').querySelectorAll('[role=\"button\"],button,div[jsname]')).find(b => /attach|adjuntar|clip/i.test((b.getAttribute('aria-label')||'')+' '+(b.getAttribute('title')||'')))")
            time.sleep(2.0)
            node = js_eval(ws, """(() => {
              const dlg = document.querySelector('div[role="dialog"]');
              if (!dlg) return 'no-dialog';
              return dlg.querySelector('input[type="file"]') ? 'ok' : 'no-file-input';
            })()""")
        if node != 'ok':
            attached.append((f, 'no-file-input'))
            continue

        # set the files directly on the hidden input
        try:
            doc = cdp('DOM.getDocument', {'depth': -1})
            root = doc['root']['nodeId']
            q = cdp('DOM.querySelector', {'nodeId': root,
                                          'selector': 'div[role="dialog"] input[type="file"]'})
            nid = q.get('nodeId', 0)
            cdp('DOM.setFileInputFiles', {'files': [os.path.abspath(f)], 'nodeId': nid})
            attached.append((f, 'set'))
            time.sleep(2.5)
        except Exception as e:
            attached.append((f, 'error:%s' % str(e)[:60]))

    # wait for the attachment chip to appear
    time.sleep(2.5)
    chip = js_eval(ws, """(() => {
      const dlg = document.querySelector('div[role="dialog"]');
      if (!dlg) return 'no-dialog';
      const t = dlg.innerText;
      return JSON.stringify({text: t.slice(0, 600)});
    })()""")
    names = []
    for f, st in attached:
        if st == 'set' and os.path.basename(f)[:18] in (chip or ''):
            names.append(os.path.basename(f))

    # ---- Send via Ctrl+Enter ----
    cdp('Input.dispatchKeyEvent', {'type': 'keyDown', 'key': 'Enter', 'code': 'Enter',
                                   'windowsVirtualKeyCode': 13, 'nativeVirtualKeyCode': 13,
                                   'modifiers': 2})
    cdp('Input.dispatchKeyEvent', {'type': 'keyUp', 'key': 'Enter', 'code': 'Enter',
                                   'windowsVirtualKeyCode': 13, 'nativeVirtualKeyCode': 13,
                                   'modifiers': 2})
    time.sleep(5)

    v = js_eval(ws, """(() => {
      const dlg = document.querySelector('div[role="dialog"]');
      const err = /specify at least one recipient/i.test(document.body.innerText);
      const toast = /Message sent/i.test(document.body.innerText);
      return JSON.stringify({dialogGone: !dlg, err, toast});
    })()""")
    ws.close()
    try:
        r = json.loads(v)
    except Exception:
        r = {}
    if r.get('err'):
        return 'RECIPIENT-ERROR'
    if r.get('dialogGone') or r.get('toast'):
        return 'sent|attached=%s' % (','.join(names) if names else 'NONE')
    return 'send-unverified|attached=%s' % (','.join(names) if names else 'NONE')


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print('usage: gmail_send_attach.py <to> <subject> <body_file> <attach> [attach...]')
        sys.exit(2)
    to = sys.argv[1]
    subject = sys.argv[2]
    body = open(sys.argv[3], encoding='utf-8').read()
    files = sys.argv[4:]
    for f in files:
        if not os.path.exists(f):
            print('MISSING FILE:', f)
            sys.exit(3)
    res = send_with_attachment(to, subject, body, files)
    print(res)
