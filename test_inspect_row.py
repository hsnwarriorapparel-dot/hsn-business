import sys, json, time
sys.path.insert(0, '/home/ubuntu')
from cdp_helper import get_tabs, connect, js_eval

tabs = get_tabs()
wa = [t for t in tabs if 'web.whatsapp.com' in (t.get('url') or '') and t.get('type') == 'page']
if not wa:
    print('NO WA TAB')
    sys.exit(1)
ws = connect(wa[0])

TARGET = "+34 661 57 14 63"
LOW = TARGET.lower()

# Inspect the chat row structure - use double braces for literal braces in f-string
js = f"""(()=>{{
  const rows=[...document.querySelectorAll('[data-testid^="list-item-"]')];
  for(const it of rows){{
    const t=((it.innerText||'')+' '+(it.textContent||'')).toLowerCase();
    if(t.includes({json.dumps(LOW)})){{
      const kids = [...it.children].map(c=>({{"tname": c.tagName, "class": c.className, "text": (c.innerText||'').slice(0,50)}})).slice(0,10);
      return JSON.stringify({{
        "tagName": it.tagName,
        "className": it.className,
        "children": kids,
        "innerHTML": it.innerHTML.slice(0,1000)
      }});
    }}
  }}
  return 'not-found';
}})()"""
result = js_eval(ws, js, await_promise=False)
print('Chat row structure:')
print(result)

ws.close()