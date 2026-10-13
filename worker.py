#!/usr/bin/env python3
"""Overnight worker: processes leads from leads.json one at a time.
Each lead: IG follow -> IG DM -> email -> WhatsApp. Logs everything."""
import sys, time, json, csv, random
sys.path.insert(0, '/home/ubuntu')
from outreach import *
from templates import build_dm, build_wa, build_email

def load_leads():
    with open('/home/ubuntu/leads.csv') as f:
        rows = list(csv.reader(f))
    header = rows[0]
    leads = []
    for r in rows[1:]:
        d = dict(zip(header, r))
        leads.append(d)
    return leads

def save_leads(leads):
    header = ['Lead ID','Name','Type','IG Username','IG Profile Link','City','Country','Phone','Phone Type','Email','Website','Status','Profile Analysis','Products Needed','Notes']
    with open('/home/ubuntu/leads.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        for l in leads:
            w.writerow([l.get('Lead ID',''), l.get('Name',''), l.get('Type',''), l.get('IG Username',''),
                        l.get('IG Profile Link',''), l.get('City',''), l.get('Country',''),
                        l.get('Phone',''), l.get('Phone Type',''), l.get('Email',''), l.get('Website',''),
                        l.get('Status',''), l.get('Profile Analysis',''), l.get('Products Needed',''), l.get('Notes','')])

def process_lead(lead):
    lid = lead['Lead ID']; name = lead['Name']
    ig = (lead.get('IG Username') or '').lstrip('@')
    phone = (lead.get('Phone') or '').replace('+','').replace(' ','')
    email = lead.get('Email') or ''
    detail = lead.get('Notes') or f"work at {name}"
    city = lead.get('City') or 'Spain'
    results = {'follow': None, 'dm': None, 'email': None, 'wa': None}

    # 1. Instagram: open profile, follow, DM
    if ig:
        if ig_open_profile(ig):
            tab = find_tab(lambda t: f'instagram.com/{ig}' in t['url'] and t['type']=='page')
            ws = connect(tab)
            # extract contact info from bio/address row (click the address link row first)
            try:
                bio = js_eval(ws, '''(async () => {
                  const addrRow = Array.from(document.querySelectorAll('header *')).filter(e => e.children.length === 0 && /wa\.me|\.com|@/.test(e.innerText||''));
                  const txt = addrRow.map(e => e.innerText).join(' | ');
                  let links = [];
                  const btn = Array.from(document.querySelectorAll('header [role="button"], header a')).find(e => /wa\.me|\.com/.test(e.innerText||''));
                  if (btn) { btn.click(); await new Promise(r=>setTimeout(r,1500)); 
                    const dlg = document.querySelector('div[role="dialog"]');
                    if (dlg) links = Array.from(dlg.querySelectorAll('a')).map(a => a.href).filter(h => /wa\.me|mailto/.test(h));
                  }
                  const close = document.querySelector('div[role="dialog"] [aria-label="Close"], div[role="dialog"] svg[aria-label*="Close"]');
                  if (close) close.click();
                  return JSON.stringify({bioText: txt.slice(0,200), links});
                })()''')
                import json as _json
                b = _json.loads(bio)
                if not phone:
                    for link in b.get('links', []):
                        if 'wa.me/' in link:
                            import re as _re
                            m = _re.search(r'wa\.me/(\d+)', link)
                            if m: lead['Phone'] = m.group(1); phone = m.group(1); break
                if not email:
                    for link in b.get('links', []):
                        if 'mailto:' in link:
                            lead['Email'] = link.split('mailto:')[1].split('?')[0]; email = lead['Email']; break
                results['bio'] = b.get('bioText', '')[:80]
            except Exception as e:
                results['bio'] = f'bio-extract-failed: {e}'
            ws.close()
            tab = find_tab(lambda t: f'instagram.com/{ig}' in t['url'] and t['type']=='page')
            ws = connect(tab)
            results['follow'] = ig_follow(ws)
            time.sleep(2)
            dm_text = build_dm(name.split('(')[0].strip(), detail)
            results['dm'] = ig_dm(ws, dm_text)
            ws.close()
        else:
            results['follow'] = 'profile-not-found'
            results['dm'] = 'skipped'

    # 2. Email
    if email:
        subject, body = build_email(name, detail)
        results['email'] = gmail_send(email, subject, body)

    # 3. WhatsApp
    if phone and len(phone) >= 11:
        wa_text = build_wa(name.split('(')[0].strip(), detail)
        results['wa'] = wa_send(phone, wa_text)

    ok = all(v in ('sent', 'ok', 'clicked', None) or (v and 'sent' in str(v)) for v in results.values())
    status = f"COMPLETE: follow={results['follow']} dm={results['dm']} email={results['email']} wa={results['wa']}"
    lead['Status'] = status
    return results

def main():
    leads = load_leads()
    queue = [l for l in leads if 'COMPLETE' not in l.get('Status','') and 'SKIP' not in l.get('Status','')]
    log(f"Starting overnight run: {len(queue)} leads in queue")
    for lead in queue:
        try:
            r = process_lead(lead)
            log(f"{lead['Lead ID']} {lead['Name']}: {r}")
        except Exception as e:
            log(f"{lead['Lead ID']} ERROR: {e}")
            lead['Status'] = f"ERROR: {e}"
        save_leads(leads)
        # anti-block delay: 3-6 min between leads
        delay = random.randint(180, 360)
        log(f"sleeping {delay}s before next lead")
        time.sleep(delay)
    log("Queue finished")

def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    with open('/home/ubuntu/outreach_log.txt', 'a') as f:
        f.write(line + "\n")
    print(line)

if __name__ == '__main__':
    main()
