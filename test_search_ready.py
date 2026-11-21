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

# Search for Shudokan
TARGET = "Shudokan"
LOW = TARGET.lower()

js = f"""(()=>{{
  const box = document.querySelector('[data-testid="chat-list-search"]') ||
              document.querySelector('[aria-label="Search"]') ||
              document.querySelector('input[type="text"]');
  if(!box) return 'no-search-box';
  box.focus();
  const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  s.call(box, {json.dumps(TARGET)});
  box.dispatchEvent(new Event('input', {{bubbles:true}}));
  return 'typed';
}})()"""
result = js_eval(ws, js, await_promise=False)
print('Search typed:', result)

time.sleep(3)

# Get search results
js = f"""(()=>{{
  const rows = [...document.querySelectorAll('[data-testid^="list-item-"]')];
  return JSON.stringify(rows.map(it=>{{
    const t = ((it.innerText||'')+' '+(it.textContent||'')).toLowerCase();
    if(t.includes({json.dumps(LOW)})) {{
      const rc = it.getBoundingClientRect();
      return {{text: (it.innerText||'').replace(/\\n/g,' | ').slice(0,200), x:rc.x+rc.width/2, y:rc.y+rc.height/2}};
    }}
    return null;
  }}).filter(Boolean);
}})()"""
results = js_eval(ws, js, await_promise=False) or '[]'
results = json.loads(results)
print(f'Search results for "{TARGET}": {len(results)}')
for r in results:
    print(f'  {r}')

# Also get all visible list items
js = """(()=>{
  const rows=[...document.querySelectorAll('[data-testid^="list-item-"]')];
  return JSON.stringify(rows.map(it=>((it.innerText||'')+' '+(it.textContent||'')).replace(/\\n/g,' | ').slice(0,200)).filter(Boolean));
})()"""
all_items = js_eval(ws, js, await_promise=False) or '[]'
all_items = json.loads(all_items)
print(f'\nAll list items ({len(all_items)}):')
for i, item in enumerate(all_items):
    print(f'  {i}: {item}')

ws.close()