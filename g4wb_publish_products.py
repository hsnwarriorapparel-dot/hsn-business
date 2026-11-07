#!/usr/bin/env python3
"""Publish the HSN Warrior Apparels product listings to go4WorldBusiness.

Fills the Add Product form for each listing and submits it.

Images are the COMPOSED listing images from /home/ubuntu/g4wb_assets/listings
(our logo + our own factory photos + typed specs) - never another client's
branded garment photos.

Run: python3 g4wb_publish_products.py [index]   (no arg = all)
"""
import sys, json, time, os
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect
import g4wb_listings as L

ADD_URL = 'https://www.go4worldbusiness.com/member/dashboard/products/new/new/0'

# listing key -> composed image (product-specific)
IMG = {
    'gi': '/home/ubuntu/g4wb_assets/listings/gi.png',
    'rashguard': '/home/ubuntu/g4wb_assets/listings/rashguard.png',
    'shorts': '/home/ubuntu/g4wb_assets/listings/shorts.png',
    'tights': '/home/ubuntu/g4wb_assets/listings/gi.png',
    'belt': '/home/ubuntu/g4wb_assets/listings/gi.png',
    'gloves': '/home/ubuntu/g4wb_assets/listings/factory.png',
    'headgear': '/home/ubuntu/g4wb_assets/listings/factory.png',
    'shinguards': '/home/ubuntu/g4wb_assets/listings/factory.png',
    'hoodie': '/home/ubuntu/g4wb_assets/listings/hoodie.png',
    'tee': '/home/ubuntu/g4wb_assets/listings/tee.png',
}
# map listing order -> image key
IMGKEY = ['gi', 'rashguard', 'shorts', 'tights', 'belt', 'gloves', 'headgear',
          'shinguards', 'hoodie', 'tee']

# select option values
UNIT_PIECE = '18'      # Piece
UNIT_PAIR = '17'       # Pair
INCOTERM_DDP = '3'     # DDP
COUNTRY_PAKISTAN = 'Pakistan'
# NOTE: rateUnit and incoterm live under [prod], not the top level.
SEL = {'[prod][rateUnit]': UNIT_PIECE, '[prod][incoterm]': INCOTERM_DDP,
       '[mfgCountry]': COUNTRY_PAKISTAN, '[deliveryTimeUnits]': UNIT_PIECE}

tabs = get_tabs()
gm = [t for t in tabs if 'mail.google' in t.get('url', '') and t.get('type') == 'page']
if not gm:
    print('NO BROWSER TAB'); sys.exit(1)
ws = connect(gm[0])
_n = [0]


def cdp(method, params=None, sid=None):
    _n[0] += 1
    mid = _n[0]
    msg = {'id': mid, 'method': method, 'params': params or {}}
    if sid:
        msg['sessionId'] = sid
    ws.send(json.dumps(msg))
    deadline = time.time() + 60
    while time.time() < deadline:
        data = json.loads(ws.recv())
        if data.get('id') == mid:
            if 'error' in data:
                raise RuntimeError(data['error'])
            return data.get('result', {})
    raise TimeoutError(method)


def ev(expr, sid):
    r = cdp('Runtime.evaluate', {'expression': expr, 'returnByValue': True}, sid)
    return r.get('result', {}).get('value')


def set_file(sid, name, path):
    doc = cdp('DOM.getDocument', {}, sid)
    q = cdp('DOM.querySelector',
            {'nodeId': doc['root']['nodeId'],
             'selector': 'input[type=file][name="%s"]' % name}, sid)
    nid = q.get('nodeId', 0)
    if not nid:
        return 'no-node'
    cdp('DOM.setFileInputFiles', {'files': [path], 'nodeId': nid}, sid)
    return 'set'


def fill(item, img_path, sid):
    P = 'member_edit_prefproduct'
    vals = {
        '%s[prod][name]' % P: item['name'],
        '%s[prod][productGrade]' % P: item['grade'],
        '%s[prod][minPrice]' % P: str(item['min_price']),
        '%s[prod][maxPrice]' % P: str(item['max_price']),
        '%s[description]' % P: item['desc'],
        '%s[deliveryTimeQty]' % P: str(item.get('delivery_time', 25)),
        '%s[deliveryTime]' % P: str(item.get('delivery_time', 25)),
        '%s[packDetails]' % P: item['pack'],
        '%s[capacity]' % P: item['capacity'],
        '%s[prod][sellercode]' % P: item['seller_code'],
        '%s[prod][standards]' % P: item['standards'],
        '%s[prod][trademarkName]' % P: item['trademark'],
        '%s[prod][loadingPort]' % P: item['loading_port'],
        '%s[prod][usageOrApplication]' % P: item['usage'],
        '%s[brand]' % P: item['brand'],
        '%s[modelNo]' % P: item['model'],
        '%s[hsCode]' % P: item['hs_code'],
    }
    for i in range(1, 5):
        if i <= len(item['specs']):
            vals['%s[keySpec%d]' % (P, i)] = item['specs'][i - 1]
    for i in range(1, 5):
        if i <= len(item['advantages']):
            vals['%s[keyAdv%d]' % (P, i)] = item['advantages'][i - 1]
    # selects
    for k, v in SEL.items():
        vals['%s%s' % (P, k)] = v
    if item['unit'] == 'Pair':
        vals['%s[prod][rateUnit]' % P] = UNIT_PAIR
    if item['moq_unit'] == 'Pairs':
        vals['%s[deliveryTimeUnits]' % P] = UNIT_PAIR
    payload = json.dumps(vals, ensure_ascii=False)
    js = """(()=>{
  const DATA=%s;
  const setVal=(el,v)=>{
    const proto=(el.tagName==='TEXTAREA')?window.HTMLTextAreaElement.prototype:window.HTMLInputElement.prototype;
    const d=Object.getOwnPropertyDescriptor(proto,'value');
    if(d&&d.set) d.set.call(el,v); else el.value=v;
    el.dispatchEvent(new Event('input',{bubbles:true}));
    el.dispatchEvent(new Event('change',{bubbles:true}));
  };
  const rep=[];
  for(const [name,val] of Object.entries(DATA)){
    const el=document.querySelector('[name="'+name.replace(/"/g,'\\\\"')+'"]');
    if(!el){rep.push('MISS '+name);continue;}
    if(el.tagName==='SELECT'){
      let ok=false;
      for(const o of el.options){ if(o.value===val||o.text===val){el.selectedIndex=o.index;ok=true;break;} }
      if(!ok){rep.push('NOOPT '+name+'='+val+' have:'+[...el.options].slice(0,4).map(o=>o.value).join(','));continue;}
      el.dispatchEvent(new Event('change',{bubbles:true}));
    } else { setVal(el,val); }
    rep.push('OK '+name);
  }
  // sample availability radio = Buyer
  const radios=[...document.querySelectorAll('input[name="'+%s+'[sample]"]')];
  if(radios.length){ radios[0].checked=true; radios[0].dispatchEvent(new Event('change',{bubbles:true})); rep.push('sample=Buyer'); }
  return JSON.stringify(rep);
})()""" % (payload, json.dumps(P))
    return ev(js, sid)


def publish(item, img_path, sid, idx):
    print('\n=== [%d] %s' % (idx, item['name'][:60]))
    st = set_file(sid, 'member_edit_prefproduct[images][0][file][file]', img_path)
    print('  image:', st)
    time.sleep(2)
    # The image slot has its OWN Upload button - selecting the file is not
    # enough, the file must be uploaded (that is what fills the hidden
    # member_edit_prefproduct[image0] field the form actually submits).
    # The image widget flow (found by reading the widget HTML):
    #   1. the "Upload" LABEL (label.imageUploadBtn) opens the file picker
    #      -> we set the file via DOM.setFileInputFiles
    #   2. that opens a CROP canvas (label.cropbtn titled "Save cropped image")
    #   3. clicking cropBtn ("Save") uploads the cropped image and fills the
    #      hidden member_edit_prefproduct[image0] field the form submits
    #   4. radio "choose_primary_0" marks it as the primary image
    print('  upload:', ev("""(()=>{
      const lbl=document.querySelector('label.imageUploadBtn[for="member_edit_prefproduct_images_0_file_file"]');
      if(!lbl) return 'no-upload-label';
      lbl.click(); return 'clicked-upload-label';
    })()""", sid))
    time.sleep(7)
    print('  crop:', ev("""(()=>{
      const cb=document.querySelector('#cropBtn_0');
      if(!cb) return 'no-crop-btn';
      cb.click(); return 'clicked-crop-save';
    })()""", sid))
    time.sleep(10)
    print('  uploaded:', ev("""(()=>{
      const h=document.querySelector('[name="member_edit_prefproduct[image0]"]');
      const prev=document.querySelector('#imageUploadedPreview_0');
      return 'image0='+(h?(h.value||'').slice(0,70):'no-hidden')+' | preview='+(prev?(prev.getAttribute('src')||'').slice(-40):'none');
    })()""", sid))
    # mark it as the primary image
    print('  primary:', ev("""(()=>{
      const r=document.querySelector('#choose_primary_0');
      if(!r) return 'no-radio';
      const box=document.querySelector('#primaryCheckboxContainer_0');
      if(box) box.style.visibility='visible';
      r.checked=true; r.dispatchEvent(new Event('change',{bubbles:true}));
      return 'ok';
    })()""", sid))
    time.sleep(2)
    rep = fill(item, img_path, sid)
    # read back the actual DOM state of the selects + a text field
    print('  state:', ev("""(()=>{
      const g=n=>{const e=document.querySelector('[name="'+n+'"]');if(!e)return '<missing>';return e.tagName+'='+(e.value||'').slice(0,40);};
      return JSON.stringify({
        name:g('member_edit_prefproduct[prod][name]'),
        grade:g('member_edit_prefproduct[prod][productGrade]'),
        min:g('member_edit_prefproduct[prod][minPrice]'),
        unit:g('member_edit_prefproduct[prod][rateUnit]'),
        incoterm:g('member_edit_prefproduct[prod][incoterm]'),
        country:g('member_edit_prefproduct[mfgCountry]'),
        desc:g('member_edit_prefproduct[description]'),
        file0:g('member_edit_prefproduct[images][0][file][file]'),
        img0:g('member_edit_prefproduct[image0]'),
        hiddenImg:[...document.querySelectorAll('input[type=hidden][name*="image"]')].map(h=>h.name+'='+h.value.slice(0,30)).join(' | '),
        radioChecked:[...document.querySelectorAll('input[type=radio]:checked')].map(r=>r.name+'='+r.value).slice(0,6).join(' | '),
      });})()""", sid))
    bad = [x for x in json.loads(rep) if x.startswith(('MISS', 'NOOPT'))]
    print('  fields set:', len(json.loads(rep)) - len(bad), '| problems:', bad[:6] if bad else 'none')
    # submit
    # The form carries read_only="" - strip it or the browser refuses to
    # submit it, which is why the banner appeared with every field filled.
    print('  unlock:', ev("""(()=>{
      const f=document.querySelector('form');
      if(!f) return 'no-form';
      const before=f.getAttribute('read_only');
      f.removeAttribute('read_only');
      f.removeAttribute('readonly');
      f.removeAttribute('novalidate');
      return 'before='+before+' after='+(f.getAttribute('read_only')||'removed');
    })()""", sid))
    # The Save Product button is name="member_edit_prefproduct[next]" -> this is
    # a MULTI-STEP wizard. Clicking it posts the form, but the site then expects
    # the form to be SUBMITTED natively (requestSubmit) rather than a synthetic
    # click. Use requestSubmit so the browser performs a real POST.
    print('  submit:', ev("""(()=>{
      const f=document.querySelector('form');
      const b=[...document.querySelectorAll('button,input[type=submit]')].find(x=>((x.innerText||x.value||'').trim().toLowerCase().replace(/\\s+/g,' ')).startsWith('save'));
      if(!b) return 'no-btn';
      if(f && f.requestSubmit){ try{ f.requestSubmit(b); return 'requestSubmit'; }catch(e){ return 'reqErr:'+e; } }
      b.click(); return 'clicked';
    })()""", sid))
    time.sleep(6)
    # a confirmation modal may appear - look for it and confirm
    print('  modal:', ev("""(()=>{
      const m=[...document.querySelectorAll('.modal,[role=dialog],dialog')].filter(e=>{
        const st=getComputedStyle(e); return st.display!=='none' && st.visibility!=='hidden' && (e.innerText||'').trim().length>10;});
      if(!m.length) return 'none';
      const t=(m[0].innerText||'').trim().replace(/\\n/g,' | ').slice(0,220);
      const btn=[...m[0].querySelectorAll('button,a')].map(b=>(b.innerText||b.value||'').trim()).filter(Boolean);
      return JSON.stringify({text:t, buttons:btn});
    })()""", sid))
    # click a confirm button inside the modal if present
    print('  confirm:', ev("""(()=>{
      const m=[...document.querySelectorAll('.modal,[role=dialog],dialog')].filter(e=>getComputedStyle(e).display!=='none'&&(e.innerText||'').trim().length>10);
      if(!m.length) return 'no-modal';
      const b=[...m[0].querySelectorAll('button,a,input[type=submit]')].find(x=>/^(confirm|yes|save|continue|ok|submit)/i.test((x.innerText||x.value||'').trim()));
      if(!b) return 'no-confirm-btn';
      b.click(); return 'clicked:'+(b.innerText||b.value||'').trim();
    })()""", sid))
    time.sleep(12)
    print('  url:', ev('location.href', sid))
    print('  msg:', ev("""(()=>{const t=document.body?document.body.innerText:'';const m=t.match(/(cannot be empty|required[^\\n]{0,50}|successfully[^\\n]{0,60}|added[^\\n]{0,50}|error[^\\n]{0,80})/gi);return m?m.slice(0,5).join(' || '):'none';})()""", sid))
    # dump the actual validation errors and which fields are flagged
    print('  banner:', ev("""(()=>{const t=document.body?document.body.innerText:'';const i=t.search(/correct the errors|errors below|please review/i);return i>=0?t.slice(Math.max(0,i-500),i+700):'no-banner';})()""", sid))
    # Which fields have a red border / is-invalid class right now?
    # what does the form itself say is required / still empty?
    print('  form:', ev("""(()=>{
      const f=document.querySelector('form');
      const req=[...document.querySelectorAll('[required]')].map(e=>(e.tagName+'|'+(e.name||e.id)+'|val='+((e.value||'').slice(0,24))+'|sel='+(e.tagName==='SELECT'?e.options[e.selectedIndex].value:'')).slice(0,110));
      const emptyReq=req.filter(x=>x.includes('val=')&&x.includes('|val=|'));
      const hidden=[...document.querySelectorAll('input[type=hidden]')].map(h=>h.name+'='+(h.value||'').slice(0,30)).filter(x=>!/_token/.test(x));
      return JSON.stringify({action:f?(f.action||'').slice(-40):'no-form', method:f?(f.method||''):'', reqCount:req.length, emptyReq:emptyReq.slice(0,10), hidden:hidden.slice(0,14)});
    })()""", sid))
    print('  invalid:', ev("""(()=>{
      const out=[];
      document.querySelectorAll('input,select,textarea').forEach(e=>{
        const cls=(e.className||'').toString();
        const st=getComputedStyle(e);
        const bad=/is-invalid|has-error|error|invalid/i.test(cls) || st.borderColor.match(/rgb\((2[0-9]{2}, ?[0-9]{1,3}, ?[0-9]{1,3})/) && e.getAttribute('aria-invalid')==='true';
        if(bad) out.push((e.name||e.id||e.tagName)+' cls='+cls.slice(0,50)+' border='+st.borderColor);
      });
      return JSON.stringify(out.slice(0,12));
    })()""", sid))
    print('  errors:', ev("""(()=>{
      const errs=[...document.querySelectorAll('.error,.invalid-feedback,.help-block,[class*=error],[class*=invalid]')]
        .map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<160);
      const bad=[...document.querySelectorAll('input,select,textarea')].filter(e=>e.classList.contains('is-invalid')||e.getAttribute('aria-invalid')==='true')
        .map(e=>e.name||e.id);
      const boxes=[...document.querySelectorAll('input[type=checkbox]:checked')].map(e=>e.name+'='+e.value);
      // every element that has a validation-ish class or aria-invalid
      const near=[...document.querySelectorAll('*')].filter(e=>{
        const c=(e.className||'').toString().toLowerCase();
        return /invalid|has-error|error/.test(c) && (e.innerText||'').trim().length<200 && (e.innerText||'').trim().length>3;
      }).map(e=>((e.className||'')+' :: '+(e.innerText||'').trim().replace(/\n/g,' | ')).slice(0,170));
      return JSON.stringify({errs:errs.slice(0,8), flagged:bad.slice(0,10), checked:boxes.slice(0,6), near:near.slice(0,12)});
    })()""", sid))


def main():
    only = int(sys.argv[1]) if len(sys.argv) > 1 else None
    items = L.build()
    for i, item in enumerate(items, 1):
        if only and i != only:
            continue
        key = IMGKEY[i - 1]
        img = IMG.get(key)
        if not img or not os.path.exists(img):
            print('SKIP [%d] no image (%s)' % (i, key)); continue
        tid = cdp('Target.createTarget', {'url': ADD_URL})['targetId']
        s = cdp('Target.attachToTarget', {'targetId': tid, 'flatten': True})['sessionId']
        cdp('Page.enable', sid=s)
        cdp('DOM.enable', sid=s)
        time.sleep(20)
        publish(item, img, s, i)
        # close the tab
        try:
            cdp('Target.closeTarget', {'targetId': tid}, s)
        except Exception:
            pass
        time.sleep(3)
    ws.close()


if __name__ == '__main__':
    main()
