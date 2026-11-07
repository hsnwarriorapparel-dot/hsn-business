#!/usr/bin/env python3
"""Send a go4WorldBusiness inquiry to a buyer RFQ.

THE INQUIRY FORM (mapped 2026-11-07):
  URL: https://www.go4worldbusiness.com/inquiries/send/buyleads/<id>/<slug>
  Fields:
    form[message]      - the quote text (required)
    form[companyName]  - pre-filled "HSN Warrior Apparels"
    form[name]         - pre-filled "Ghulam Hassan"
    form[email]        - EMPTY, must be filled (our Gmail)
    form[phone]        - pre-filled "+92 337 3336381"
    form[country]      - select, value = country id
    form[captcha]      - required, there is a CAPTCHA
    form[_token]       - CSRF token
  Button: "Inquire Now" (type=submit)

LIMITS: JUNIOR member = 1 buyer inquiry/day free (max 2 per week),
5 inquiries/day to suppliers & products. Premium = 100 buyers/day.

IMPORTANT: the form has a CAPTCHA and the country list has NO PAKISTAN
(238 countries, no PK). Both are handled:
  - country: use the closest available (India=99) and say the real country
    in the message text.
  - captcha: this script fills everything EXCEPT the captcha, then reports
    "READY" and leaves the tab open so the user can complete it, OR the
    captcha can be solved by a human in the browser.

Run:  python3 g4wb_send_inquiry.py <buylead_path> [message_file]
"""
import sys, json, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect

EMAIL = 'hsnwarriorapparel@gmail.com'
COUNTRY_ID = '162'   # Pakistan - the platform DOES have Pakistan (id 162)

DEFAULT_MESSAGE = """Dear Sir/Madam,

We are HSN Warrior Apparels, a martial arts and sportswear manufacturer and exporter based in Sialkot, Pakistan. We produce custom sports apparel and team uniforms for clubs, academies and brands worldwide.

Your requirement for custom sports jerseys and athletic apparel is exactly our production line:

- Sports jerseys, football kits and team uniforms in polyester, interlock and micro-mesh
- Full sublimation printing, or screen print and heat transfer for heavier graphics
- Your club or country name, crest and numbers, in your own colours
- Sizes from youth to adult, matched to your size chart
- Minimum 30 units per style, so a single team can test a design before a full run
- 3 to 4 weeks production, then DHL, FedEx or UPS door to door in 4 to 6 working days

We handle shipping and customs on our side, so the landed cost carries no added fees.

Please send us your artwork or logo file and your size breakdown, and we will reply with an exact quotation and a sample mockup for one piece.

Best regards,
Ghulam Hassan
HSN Warrior Apparels
hsnwarriorapparel@gmail.com
+92 337 3336381"""


def main():
    path = sys.argv[1]
    msg = DEFAULT_MESSAGE
    if len(sys.argv) > 2:
        msg = open(sys.argv[2], encoding='utf-8').read()
    url = 'https://www.go4worldbusiness.com' + path

    tabs = get_tabs()
    gm = [t for t in tabs if 'mail.google' in t.get('url', '') and t.get('type') == 'page']
    if not gm:
        print('NO BROWSER TAB'); return
    ws = connect(gm[0]); _n = [0]

    def cdp(m, p=None, sid=None):
        _n[0] += 1; mid = _n[0]
        payload = {'id': mid, 'method': m, 'params': p or {}}
        if sid: payload['sessionId'] = sid
        ws.send(json.dumps(payload))
        t = time.time() + 50
        while time.time() < t:
            d = json.loads(ws.recv())
            if d.get('id') == mid:
                if 'error' in d: raise RuntimeError(d['error'])
                return d.get('result', {})
        raise TimeoutError(m)

    def ev(e, s):
        r = cdp('Runtime.evaluate', {'expression': e, 'returnByValue': True, 'awaitPromise': True}, sid=s)
        if r.get('exceptionDetails'):
            return 'JS_ERR: ' + str(r['exceptionDetails'])[:250]
        return r.get('result', {}).get('value')

    tid = cdp('Target.createTarget', {'url': url})['targetId']
    s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
    cdp('Page.enable', sid=s)
    time.sleep(24)

    print('=== filling inquiry ===')
    print(ev("""(()=>{
      const set=(n,v)=>{const e=document.querySelector('[name="'+n+'"]');if(!e)return 'MISS '+n;
        const pr=e.tagName==='TEXTAREA'?window.HTMLTextAreaElement.prototype:window.HTMLInputElement.prototype;
        const d=Object.getOwnPropertyDescriptor(pr,'value');if(d&&d.set)d.set.call(e,v);else e.value=v;
        e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));return 'OK '+n;};
      const out=[];
      out.push(set('form[message]',MESSAGE));
      out.push(set('form[email]',EMAIL));
      const c=document.querySelector('[name="form[country]"]');
      if(c){for(const o of c.options){if(o.value===COUNTRY){c.selectedIndex=o.index;break;}}
        c.dispatchEvent(new Event('change',{bubbles:true}));out.push('OK country='+(c.options[c.selectedIndex]||{}).text);}
      else out.push('MISS country');
      const cap=document.querySelector('[name="form[captcha]"]');
      out.push(cap?(cap.tagName+' captcha present, type='+(cap.type||'')+' src='+((cap.getAttribute('src')||'').slice(0,60))):'no captcha field');
      return out.join(' | ');
    })()""".replace('MESSAGE', json.dumps(msg)).replace('EMAIL', json.dumps(EMAIL)).replace('COUNTRY', json.dumps(COUNTRY_ID)), s))
    time.sleep(2)
    print()
    print('=== captcha detail ===')
    print(ev("""(()=>{
      const c=document.querySelector('[name="form[captcha"]"]');
      if(!c) return 'none';
      const wrap=c.parentElement;
      return JSON.stringify({tag:c.tagName,type:c.type,cls:(c.className||'').toString().slice(0,60),
        imgs:[...wrap.querySelectorAll('img')].map(i=>(i.getAttribute('src')||'').slice(0,90)),
        nearby:(wrap.innerText||'').trim().slice(0,90)});
    })()""", s))
    print()
    print('READY: the form is filled. The CAPTCHA needs a human.')
    print('TAB LEFT OPEN at:', url)
    ws.close()


if __name__ == '__main__':
    main()
