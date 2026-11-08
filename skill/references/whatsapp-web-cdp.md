# WHATSAPP WEB VIA CDP - THE SELECTORS THAT ACTUALLY WORK

## THE SCROLL BUG - THE ONE THAT SILENTLY EATS EVERY REPLY

The chat row for TOWASAN sat at **y=1174** in a **970px viewport**. Every
click - both `element.click()` and a real CDP mouse event - landed
OUTSIDE the window and did nothing.

The trap: the composer element
`[data-testid="conversation-compose-box-input"]` was ALREADY in the DOM
(WhatsApp keeps it mounted), so a naive check reported "conversation
open: yes" while nothing was actually loaded. The verification read
`composerPresent` instead of asking whether the chat was open.

**ALWAYS `scrollIntoView({block:'center'})` the row first, then re-read
its bounding box, then click.**

```js
it.scrollIntoView({block:'center', behavior:'instant'});
const rc = it.getBoundingClientRect();   // re-read AFTER the scroll
return {x: rc.x + rc.width/2, y: rc.y + rc.height/2};
```

## THE CHAT ROW SELECTOR

`div[role="listitem"]` returns **0** on the current build. The chat rows
carry a `data-testid`:

```js
document.querySelectorAll('[data-testid^="list-item-"]')
```

Each row is `data-testid="list-item-N"`. The chat title inside it is a
`span[title]`.

## THE COMPOSER IS A CONTENTEDITABLE DIV - NOT AN INPUT

```html
<div data-testid="conversation-compose-box-input"
     contenteditable="true" data-tab="10"
     aria-label="Type a message to +49 89 4315508">
```

There is **no `.value`**. Setting
`Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set`
does nothing - it is the wrong prototype.

The working method:

```js
const inp = document.querySelector('[data-testid="conversation-compose-box-input"]');
inp.focus();
const proto = Object.getPrototypeOf(inp);
const desc = Object.getOwnPropertyDescriptor(proto, 'textContent');
if (desc && desc.set) desc.set.call(inp, msg); else inp.textContent = msg;
inp.dispatchEvent(new InputEvent('input', {bubbles:true, inputType:'insertText', data:msg}));
inp.dispatchEvent(new Event('change', {bubbles:true}));
```

Note the `textContent` setter has to be taken from the ELEMENT's own
prototype, not from `HTMLElement.prototype` - React installs its own
property on the instance's prototype chain.

## PASS THE TEXT THROUGH A GLOBAL, NOT STRING SUBSTITUTION

Substituting a 1,500-character message into the JS source with
`.replace('MSG', json.dumps(MSG))` produced a silent `None` return. Pass it
as a global instead:

```python
js_eval(ws, 'window.__waMsg = ' + json.dumps(MSG) + '; 1', await_promise=False)
# then in JS: const msg = window.__waMsg || '';
```

## THE `aria-label` IS THE VERIFICATION

`aria-label="Type a message to +49 89 4315508"` tells you WHICH chat is
open. **Check it against the lead's phone number before sending.** A
composer is present for every chat; only the label identifies it.

## CLEARING THE COMPOSER

Setting `textContent=''` does not clear it - React re-renders the old
value. What works is select-all + Backspace:

```js
const sel=window.getSelection(); const range=document.createRange();
range.selectNodeContents(inp); sel.removeAllRanges(); sel.addRange(range);
```
then dispatch `Input.dispatchKeyEvent` for `Backspace`.

## THE SEND BUTTON

`[data-testid="compose-btn-send"]` / `span[data-icon="send"]` /
`button[aria-label="Send"]`. It only appears once there IS text, so
"no-send-button" means "the text did not land".

## TOOLING

- `wa_open_conversation.py <name>` - opens a chat by name (with the scroll
  fix) and reports the composer label + last rows
- `wa_read_conversation.py <name>` - opens and dumps the conversation
- `wa_send_open_chat.py <name> <msg-file>` - opens, types, sends and
  verifies

## THE PROOF (2026-11-08, TOWASAN Karate Schulen)

```
conversation open: yes
type: typed:1504
composer now: {"len":1504,"head":"TOWASAN team,\\n\\nShort answer: we do not run classes..."}
send: clicked-send
after: {"composerEmpty":true,"tail":[... "TOWASAN team,... Read more\n1:20 AM"]}
```

The message is in the thread. Before this, the same conversation had been
"open" in every script while nothing was ever sent.
