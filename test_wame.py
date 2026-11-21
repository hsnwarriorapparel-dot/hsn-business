import sys, json, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval, make_cdp

tabs = get_tabs()
wa = [t for t in tabs if 'web.whatsapp.com' in (t.get('url') or '') and t.get('type') == 'page']
if not wa:
    print('NO WA TAB')
    sys.exit(1)
ws = connect(wa[0])
cdp = make_cdp(ws)

# Navigate to wa.me link for Shudokan
phone = "34661571463"
cdp('Page.navigate', {'url': f'https://wa.me/{phone}'})
time.sleep(5)

# Check if we're on the WhatsApp Web chat page or the wa.me landing page
js = """(()=>window.location.href)()"""
url = js_eval(ws, js, await_promise=False)
print('Current URL:', url)

# If on wa.me page, click "Continue to Chat"
js = """(()=>{
  const btn = document.querySelector('a[href*="web.whatsapp.com"]') || 
              document.querySelector('button:contains("Continue")') ||
              document.querySelector('a:contains("Continue")');
  if(btn) { btn.click(); return 'clicked'; }
  return 'not-found';
})()"""
result = js_eval(ws, js, await_promise=False)
print('Continue click:', result)

time.sleep(5)

# Check if chat opened
js = """(()=>!!document.querySelector('[data-testid="conversation-compose-box-input"]'))()"""
opened = js_eval(ws, js, await_promise=False)
print('Chat opened:', opened)

ws.close()