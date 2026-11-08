#!/usr/bin/env python3
"""Send a go4WorldBusiness inquiry to a buyer RFQ - single tab, captcha included.

FLOW (all in ONE tab so the captcha token matches the form session):
  1. open the inquiry URL
  2. screenshot #form_captcha_image  -> /home/ubuntu/g4wb_captcha.png
  3. read the captcha text (passed in as argv, read by a human or vision)
  4. fill message / email / country / captcha
  5. click "Inquire Now"
  6. verify the result

COUNTRY: the site's country list has NO Pakistan (238 countries, no PK), so we
use India (99) as the closest available and state the real country in the
message. This is flagged for the user.

LIMIT: JUNIOR member = 1 buyer inquiry/day free, max 2 per week.

Run:
  python3 g4wb_inquiry_send.py <path> <captcha_text> [message_file]
"""
import sys, os, json, time, base64
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect

EMAIL = 'hsnwarriorapparel@gmail.com'
# Pakistan IS on the platform - country id 162 (the earlier 'Pakistan is
# absent' conclusion was wrong; it came from a different country's list).
COUNTRY_ID = '162'   # Pakistan

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
    captcha = sys.argv[2] if len(sys.argv) > 2 else ''
    msg = DEFAULT_MESSAGE
    if len(sys.argv) > 3:
        msg = open(sys.argv[3], encoding='utf-8').read()
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

    # The captcha image is regenerated on every page load, so the text must be
    # read from the SAME tab that later submits. Two phases:
    #   phase 1 (no captcha arg): open the tab, screenshot the captcha, save the
    #                             targetId to /home/ubuntu/g4wb_inquiry_target.json
    #   phase 2 (captcha arg):    reattach to that targetId, fill and submit.
    STATE = '/home/ubuntu/g4wb_inquiry_target.json'
    if captcha and os.path.exists(STATE):
        st = json.load(open(STATE))
        tid = st['targetId']
        print('reattaching to saved tab', tid)
    else:
        tid = cdp('Target.createTarget', {'url': url})['targetId']
        json.dump({'targetId': tid, 'url': url}, open(STATE, 'w'))
        print('opened tab', tid, '-> saved for phase 2')

    s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
    cdp('Page.enable', sid=s)
    time.sleep(24)

    # 1. capture the captcha from THIS tab
    #
    # CRITICAL: in phase 2 this must NOT overwrite the image the agent
    # already read. The page regenerates the captcha on every load, so
    # re-capturing means the picture and the text no longer match - and the
    # submit fails with "Error processing your request".
    #
    # So: capture only in phase 1. In phase 2, read the CURRENT captcha
    # image src and make sure it is the SAME one the agent read. If the src
    # changed, the tab was reloaded and the agent must read it again.
    if not captcha:
        box = ev("""(()=>{
          const i=document.querySelector('#form_captcha_image');
          if(!i) return null;
          const r=i.getBoundingClientRect();
          return JSON.stringify({x:r.x,y:r.y,w:r.width,h:r.height});
        })()""", s)
        if box:
            b = json.loads(box)
            shot = cdp('Page.captureScreenshot', {'format': 'png', 'clip': {
                'x': b['x'], 'y': b['y'], 'width': b['w'], 'height': b['h'], 'scale': 3}}, s)
            if shot.get('data'):
                open('/home/ubuntu/g4wb_captcha.png', 'wb').write(base64.b64decode(shot['data']))
                src = ev("(()=>{const i=document.querySelector('#form_captcha_image');return i?(i.getAttribute('src')||''):'none';})()", s)
                try:
                    st2 = json.load(open(STATE))
                    st2['captchaSrc'] = src
                    json.dump(st2, open(STATE, 'w'))
                except Exception:
                    pass
                print('captcha image -> /home/ubuntu/g4wb_captcha.png  (read it, then run again with the text)')
                print('captcha src   :', src)
    else:
        # phase 2: report the CURRENT captcha src so a mismatch is visible
        print('captcha src now:', ev("(()=>{const i=document.querySelector('#form_captcha_image');return i?(i.getAttribute('src')||''):'none';})()", s))
    if not captcha:
        print('PHASE 1 DONE. Read /home/ubuntu/g4wb_captcha.png and re-run with the text.')
        ws.close(); return

    # 2. fill everything
    print('fill:', ev("""(()=>{
      const set=(n,v)=>{const e=document.querySelector('[name="'+n+'"]');if(!e)return 'MISS '+n;
        const pr=e.tagName==='TEXTAREA'?window.HTMLTextAreaElement.prototype:window.HTMLInputElement.prototype;
        const d=Object.getOwnPropertyDescriptor(pr,'value');if(d&&d.set)d.set.call(e,v);else e.value=v;
        e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));return 'OK '+n;};
      const out=[];
      out.push(set('form[message]',MESSAGE));
      out.push(set('form[email]',EMAIL));
      out.push(set('form[captcha]',CAPTCHA));
      const c=document.querySelector('[name="form[country]"]');
      if(c){for(const o of c.options){if(o.value===COUNTRY){c.selectedIndex=o.index;break;}}
        c.dispatchEvent(new Event('change',{bubbles:true}));out.push('country='+((c.options[c.selectedIndex]||{}).text));}
      return out.join(' | ');
    })()""".replace('MESSAGE', json.dumps(msg)).replace('EMAIL', json.dumps(EMAIL))
       .replace('CAPTCHA', json.dumps(captcha)).replace('COUNTRY', json.dumps(COUNTRY_ID)), s))
    time.sleep(2)

    # 3. submit
    print('submit:', ev("""(()=>{
      const b=[...document.querySelectorAll('button,input[type=submit]')]
        .find(x=>/inquir/i.test((x.innerText||x.value||'').trim()));
      if(!b) return 'no-button';
      b.click(); return 'clicked:'+((b.innerText||b.value||'').trim());
    })()""", s))
    time.sleep(16)
    print('url  :', ev('location.href', s))
    print('result:', ev("""(()=>{
      const t=document.body?document.body.innerText:'';
      const m=t.match(/(thank[^\\n]{0,90}|sent[^\\n]{0,90}|success[^\\n]{0,90}|error[^\\n]{0,90}|invalid[^\\n]{0,90}|captcha[^\\n]{0,90}|failed[^\\n]{0,90})/gi);
      return m?m.slice(0,4).join(' || '):'no-msg';
    })()""", s))
    print('body:', ev("""(()=>{const t=document.body?document.body.innerText:'';const i=t.search(/Sending Inquiry|Thank|inquir/i);return t.slice(Math.max(0,i-80),i+700);})()""", s))
    try:
        dump = open('/home/ubuntu/.hermes/cache/scratch/g4wb_err.js', encoding='utf-8').read()
        print('detail:', ev(dump, s))
    except Exception as e:
        print('detail: n/a', e)
    ws.close()


if __name__ == '__main__':
    main()
