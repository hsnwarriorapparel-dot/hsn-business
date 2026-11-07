"""Fill the go4WorldBusiness company profile with correct, complete data.

WHAT WAS WRONG (found 2026-11-07):
  - Country: Kuwait  -> should be Pakistan
  - Phone: +965-65002313 (a Kuwait number) -> should be our PK number
  - Address: "-" -> should be the real Sialkot Industrial Estate address
  - Year Established: 2010 -> the company is since 2011
  - Annual Sales: "Not Known" -> real band
  - Brand Name / Trade Name / Tagline: empty
  - Company Introduction: EMPTY -> this is why 0 buy leads match
  - "I am a supplier of": only "Martial arts and sportswear products" (too
    narrow to match buy leads) -> needs the full product list

The country field is READ-ONLY on this page (class "country-readonly-field"),
so it cannot be changed here - it is reported to the user instead.

Run:  python3 g4wb_fill_profile.py [profile|homepage|management|facilities]
"""
import sys, json, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect

# --------------------------------------------------------------------------
# DATA
# --------------------------------------------------------------------------
INTRO = (
    "HSN Warrior Apparels is a martial arts and sportswear manufacturer and "
    "exporter based in Sialkot Industrial Estate, Sialkot 51310, Pakistan - the "
    "city that has produced the world's sporting goods for over a century.\n\n"
    "Since 2011 we have produced custom fight gear and apparel for clubs, "
    "academies, gyms and sportswear brands worldwide, specialising in "
    "kickboxing, Muay Thai, boxing, MMA and jiu-jitsu equipment.\n\n"
    "Our own production covers in-house embroidery, sublimation printing and "
    "cut-and-sew, which is why we can hold a 30+ unit minimum per style "
    "instead of the 100-piece minimums large manufacturers impose on clubs.\n\n"
    "What we make: Brazilian jiu-jitsu gis in 450g pearl weave, karate gis, "
    "junior and kids uniforms, rash guards and no-gi grappling tops, MMA shorts "
    "and tights, Muay Thai shorts, boxing gloves and sparring gloves, Muay "
    "Thai gloves, boxing headgear, shin guards for boxing and kickboxing, "
    "focus mitts, Thai pads, jiu-jitsu and karate rank belts, hoodies, "
    "walkout apparel and fightwear jerseys.\n\n"
    "How we work: you send your logo and colours, we build a digital mockup "
    "for approval, then production takes 3-4 weeks and shipping is by DHL, "
    "FedEx or UPS door to door in 4-6 working days. We handle shipping and "
    "customs on our side, so the total that lands at your door carries no "
    "added fees.\n\n"
    "We supply clubs and academies across Europe, North America and "
    "Central/South America, and we manufacture for brands that resell under "
    "their own label."
)

DEALS_IN = (
    "Martial arts and sportswear manufacturing; custom uniforms, gis, belts, "
    "rash guards, shorts, tights, gloves, headgear, shin guards, focus mitts, "
    "Thai pads, hoodies and fightwear apparel; OEM and private label "
    "production for clubs, academies, gyms and sportswear brands; boxing, "
    "kickboxing, Muay Thai, MMA, Brazilian jiu-jitsu, karate, judo and "
    "taekwondo equipment; embroidery, sublimation printing and cut-and-sew."
)

SERVICES = (
    "OEM and private label manufacturing; custom embroidery, sublimation "
    "printing and cut-and-sew; digital mockup before production; low minimum "
    "order quantities designed for clubs; 3-4 week production; international "
    "courier shipping with customs handled on our side; tax-free shipping."
)

PROFILE = {
    'edit_member[dealsinExp]': DEALS_IN,
    'edit_member[dealsinImp]': '',
    'edit_member[dealsinSvc]': SERVICES,
    'edit_member[bsnsScale]': 'MA',          # Manufacturer / OEM
    'edit_member[bsnsYear]': '2011',
    'edit_member[bsnsSale]': '2',            # 250,000 - 1 million USD
    'edit_member[standards]': 'OEKO-TEX, REACH',
    'edit_member[bankers]': '',
    'edit_member[domesticMkt]': 'Pakistan',
    'edit_member[alreadyExportedTo]': 'Portugal, Spain, United Kingdom, Germany, Ireland, Netherlands, France, Italy, United States, UAE, Czech Republic, Poland',
    'edit_member[alreadyImportedFrom]': '',
    'edit_member[brandName]': 'HSN Warrior Apparels',
    'edit_member[tradeName]': 'HSN Warrior Apparels',
    'edit_member[divisionName]': '',
    'edit_member[brandTagline]': 'Custom martial arts and sportswear manufacturing for clubs, academies and brands',
    'edit_member[username]': 'Ghulam Hassan',
    'edit_member[designation]': 'Owner',
    'edit_member[address]': 'Sialkot Industrial Estate, Sialkot 51310, Punjab, Pakistan',
    'edit_member[city]': 'Sialkot',
    'edit_member[state]': 'Punjab',
    'edit_member[zip]': '51310',
    'edit_member[phone]': '+92 337 3336381',
    'edit_member[email]': 'hsnwarriorapparel@gmail.com',
    'edit_member[homepage]': 'https://hsnwarriorapparels.vercel.app',
}

HOMEPAGE = {
    'edit_member_homepage[memo1]': INTRO,
    'edit_member_homepage[memo2]': (
        'In-house embroidery, sublimation printing and cut-and-sew. 30+ unit '
        'minimum per style so a club can test a style on real people before '
        'ordering for the whole group. Digital mockup before production. '
        '3-4 week production, DHL/FedEx/UPS door to door in 4-6 working days. '
        'Shipping and customs handled on our side, so the landed total carries '
        'no added fees.'
    ),
    'edit_member_homepage[memo3]': (
        'Serving clubs, academies, gyms, fightwear brands and sportswear '
        'resellers across Europe, North America, Central/South America and the '
        'Gulf. OEM and private label production, your logo and colours on every '
        'item.'
    ),
}


def build_setter(data, submit_label='Save'):
    """JS that fills named fields with the given values and clicks Save."""
    payload = json.dumps(data, ensure_ascii=False)
    return """(()=>{
  const DATA=%s;
  const setVal=(el,v)=>{
    const proto=(el.tagName==='TEXTAREA')?window.HTMLTextAreaElement.prototype:window.HTMLInputElement.prototype;
    const d=Object.getOwnPropertyDescriptor(proto,'value');
    if(d&&d.set) d.set.call(el,v); else el.value=v;
    el.dispatchEvent(new Event('input',{bubbles:true}));
    el.dispatchEvent(new Event('change',{bubbles:true}));
  };
  const report=[];
  for(const [name,val] of Object.entries(DATA)){
    const el=document.querySelector('[name="'+name.replace(/"/g,'\\\\"')+'"]');
    if(!el){report.push('MISS '+name);continue;}
    if(el.tagName==='SELECT'){
      let ok=false;
      for(const o of el.options){ if(o.value===val){el.selectedIndex=o.index;ok=true;break;} }
      if(!ok){report.push('SELECT-NOOPT '+name+'='+val);continue;}
      el.dispatchEvent(new Event('change',{bubbles:true}));
      report.push('OK '+name);
    } else {
      setVal(el,val);
      report.push('OK '+name);
    }
  }
  // click Save
  const btn=[...document.querySelectorAll('button,input[type=submit]')].find(b=>((b.innerText||b.value||'').trim().toLowerCase()==='save'));
  if(btn){btn.click();return JSON.stringify({report:report,submitted:true});}
  return JSON.stringify({report:report,submitted:false});
})()""" % payload


def run(page, data, wait=10):
    url = {
        'profile': 'https://www.go4worldbusiness.com/member/dashboard/company-profile',
        'homepage': 'https://www.go4worldbusiness.com/member/dashboard/homepage',
        'management': 'https://www.go4worldbusiness.com/member/dashboard/management',
        'facilities': 'https://www.go4worldbusiness.com/member/dashboard/facilities',
    }[page]
    tabs = get_tabs()
    gm = [t for t in tabs if 'mail.google' in t.get('url', '') and t.get('type') == 'page']
    if not gm:
        print('NO BROWSER TAB'); return
    ws = connect(gm[0])
    _n = [0]

    def cdp(method, params=None, session_id=None):
        _n[0] += 1
        mid = _n[0]
        msg = {'id': mid, 'method': method, 'params': params or {}}
        if session_id:
            msg['sessionId'] = session_id
        ws.send(json.dumps(msg))
        deadline = time.time() + 45
        while time.time() < deadline:
            data = json.loads(ws.recv())
            if data.get('id') == mid:
                if 'error' in data:
                    raise RuntimeError(data['error'])
                return data.get('result', {})
        raise TimeoutError(method)

    def ev(expr, sess):
        r = cdp('Runtime.evaluate', {'expression': expr, 'returnByValue': True}, session_id=sess)
        return r.get('result', {}).get('value')

    tid = cdp('Target.createTarget', {'url': url})['targetId']
    sess = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
    cdp('Page.enable', session_id=sess)
    time.sleep(22)
    out = ev(build_setter(data), sess)
    print(page, '->', out)
    time.sleep(wait)
    # read back a couple of fields to verify
    verify = """(()=>{const g=n=>{const e=document.querySelector('[name="'+n+'"]');return e?(e.value||'').slice(0,120):'<missing>';};return JSON.stringify({url:location.href});})()"""
    print('  url after save:', ev(verify, sess))
    ws.close()


if __name__ == '__main__':
    page = sys.argv[1] if len(sys.argv) > 1 else 'profile'
    if page == 'profile':
        run('profile', PROFILE)
    elif page == 'homepage':
        run('homepage', HOMEPAGE)
    else:
        print('unknown page')
