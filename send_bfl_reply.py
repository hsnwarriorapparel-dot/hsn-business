#!/usr/bin/env python3
"""Send Brazilian Fight Lisboa reply with verify-first protocol."""
import sys, time, json
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import *
from outreach import wa_send

PHONE = "351910349061"
MSG = """Olá, obrigado pela resposta! Fabricamos kimonos de Jiu-Jitsu, rashguards e equipamento de kickboxing/muay thai, tudo com a marca da academia e em preços de fábrica. Quantas peças precisam para começar?

— HSN Warrior Apparels"""

# STEP 1: verify header BEFORE sending
tab = find_tab(lambda t: 'web.whatsapp' in t['url'] and t['type'] == 'page')
ws = connect(tab)
cdp = make_cdp(ws)
cdp("Page.enable")
cdp("Page.navigate", {"url": f"https://web.whatsapp.com/send?phone={PHONE}"})
time.sleep(15)
v = js_eval(ws, '''(() => {
  const main = document.querySelector('#main');
  const t = main ? main.innerText : '';
  return JSON.stringify({
    header: t.slice(0, 40),
    hasReply: t.includes('entraremos em contato'),
    hasPrices: t.includes('65')
  });
})()''')
print("STEP 1 - verify:", v)
d = json.loads(v)
ws.close()

# confirm it's their chat: their 2:33 AM reply must be present
if not (d['hasReply'] or d['hasPrices']):
    print("WRONG CHAT - ABORT")
    sys.exit(1)

# STEP 2: send
r = wa_send(PHONE, MSG)
print("STEP 2 - send:", str(r)[:90])
