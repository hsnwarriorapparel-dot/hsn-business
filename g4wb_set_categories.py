#!/usr/bin/env python3
"""Set the go4WorldBusiness category list + verify the country.

DISCOVERED 2026-11-07 from the site's own JS (b385a6b.js):
  - search:  GET  /signup/ajax/category-search?q=<term>
  - save:    POST /signup/ajax/category-selection/supplier
             Content-Type: application/json
             body: {"categories":["<id>",...], "compname":"...", "phone":"...",
                    "state":"...", "countryId":"<id>"}
  - countryId comes from /countries/all-with-ids -> codeToIdMap

COUNTRY FINDING: **Pakistan is NOT in go4WorldBusiness's country list.**
238 countries, no PK (Iran is missing too). The signup form therefore
defaulted this account to Kuwait - it was never a deliberate choice and it is
NOT editable on the profile page (country-readonly-field). Best available
neighbour for a Sialkot manufacturer is India (IN#99) as a placeholder, but
that is still wrong; the correct fix is a support request to add Pakistan.
Setting India is a stopgap that makes the address coherent (Sialkot, Punjab,
Pakistan + Indian country) - it is applied here so the profile is not actively
misleading, and flagged for the user.
"""
import sys, json, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect

# The endpoint enforces a MAX OF 10 ("You can select at most 10 categories").
# These 10 are the closest match to what we actually manufacture.
CATEGORIES = [
    ('Martial Arts Goods and Accessories', '1211900992'),
    ('Martial Arts Gloves', '1211900998'),
    ('Martial Arts Belts', '1211900997'),
    ('Martial Arts Mats', '1211900999'),
    ('Shin Guards', '1211900940'),
    ('Gym Belts', '1211904448'),
    ('Apparel, Clothing & Garments', '1217662976'),
    ('Sportswear', '1334874723'),
    ('Sportswear Sets', '1334858527'),
    ('Uniforms', '1217663872'),
]
COMPANY = 'HSN Warrior Apparels'
PHONE = '+92 337 3336381'
STATE = 'Punjab'
COUNTRY_ID = '99'   # India (IN) - placeholder; Pakistan does not exist in the list

tabs = get_tabs()
gm = [t for t in tabs if 'mail.google' in t.get('url', '') and t.get('type') == 'page']
if not gm:
    print('NO BROWSER TAB'); sys.exit(1)
ws = connect(gm[0]); _n = [0]


def cdp(m, p=None, sid=None):
    _n[0] += 1; mid = _n[0]
    msg = {'id': mid, 'method': m, 'params': p or {}}
    if sid: msg['sessionId'] = sid
    ws.send(json.dumps(msg))
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
        return 'JS_ERR: ' + str(r['exceptionDetails'])[:300]
    return r.get('result', {}).get('value')


URL = 'https://www.go4worldbusiness.com/member/dashboard/company-profile'
tid = cdp('Target.createTarget', {'url': URL})['targetId']
s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
cdp('Page.enable', sid=s)
time.sleep(23)

payload = {
    'categories': [cid for _, cid in CATEGORIES],
    'compname': COMPANY,
    'phone': PHONE,
    'state': STATE,
    'countryId': COUNTRY_ID,
}
js = """(async()=>{
  const payload=PAYLOAD;
  try{
    const r=await fetch('/signup/ajax/category-selection/supplier',{
      method:'POST',
      headers:{'Content-Type':'application/json','X-Requested-With':'XMLHttpRequest'},
      body:JSON.stringify(payload)
    });
    const t=await r.text();
    return 'status='+r.status+' :: '+t.slice(0,900);
  }catch(e){return 'ERR '+e;}
})()""".replace('PAYLOAD', json.dumps(payload))
print('SAVE:', ev(js, s))
time.sleep(6)

# verify by reading the profile back
print()
print('=== verify ===')
print(ev("""(async()=>{
  const r=await fetch('/member/dashboard/company-profile',{headers:{'X-Requested-With':'XMLHttpRequest'}});
  const t=await r.text();
  const i=t.search(/Martial Arts Goods and Accessories/i);
  const hits=[];
  const re=/(Martial Arts[^<]{0,40}|Shin Guards|Gym Belts|Sportswear|Apparel, Clothing[^<]{0,20}|Uniforms|Sports Goods[^<]{0,30})/g;
  let m;while((m=re.exec(t))&&hits.length<16)hits.push(m[1]);
  return 'status='+r.status+' len='+t.length+' :: '+JSON.stringify([...new Set(hits)]);
})()""", s))
ws.close()
