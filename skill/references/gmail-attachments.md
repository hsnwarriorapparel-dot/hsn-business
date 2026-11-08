# Gmail attachments via CDP


## THE ATTACHMENT REPORT WAS ALWAYS WRONG

`gmail_send_attach.py` printed `attached=NONE` on every send, even though
the files were attached and the sent row confirmed `has attachment`.

The check looked for the filename inside the compose dialog's
`innerText`. That text DOES contain it - but the chip filename sits in a
specific ancestor, and the shape of the value being compared was wrong.

**The reliable signal is the chip ELEMENT.** Gmail renders one
`[aria-label="Remove attachment"]` button per attached file. The
filename lives a few ancestors up, in the `.dL` row:

```javascript
for (const b of dlg.querySelectorAll('[aria-label*="Remove attachment"]')) {
  let n = b, t = '';
  for (let i = 0; i < 6 && n; i++) {
    const s = (n.innerText || '');
    if (/[^\n]+\.[A-Za-z0-9]{1,5}/.test(s)) { t = s; break; }
    n = n.parentElement;
  }
  const m = t.match(/([^\n]+\.[A-Za-z0-9]{1,5})/);
  if (m) out.push(m[1].trim());
}
```

Now it reports `attached=HSN_Price_List.pdf` and the sent row agrees.

**The real proof is always the SENT ROW, not the script's own report.**
Read it back with `reply_engine.gmail_rows('in:sent to:<address>')` and
look for `has attachment`.

### VERIFYING THE ATTACH PATH WITHOUT SENDING

A compose dialog left open can be inspected directly - set the file on
the hidden input and read the chip:

```python
doc = cdp('DOM.getDocument', {'depth': -1})
root = doc['root']['nodeId']
q = cdp('DOM.querySelector', {'nodeId': root,
                              'selector': 'div[role="dialog"] input[type="file"]'})
cdp('DOM.setFileInputFiles', {'files': [abspath(f)], 'nodeId': q['nodeId']})
time.sleep(3)
```

Then read the chip and discard the draft with the `[aria-label*="Discard"]`
button. Do NOT use the account's own address as a test recipient -
Gmail refuses it with `recipient-not-registered`.

