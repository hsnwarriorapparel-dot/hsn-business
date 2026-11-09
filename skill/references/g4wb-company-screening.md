# Screening go4WorldBusiness buyer companies

## THE SCREEN USED THE WRONG SKIP LIST - IT HID 51 REAL BUYERS

`screen_buyers.py` skipped every company the REACH campaign had marked
`processed`. But `processed` means the company was CONTACTED - it does
not mean its profile was READ. 330 companies had been contacted and
never screened, and that pool held real buyers ('Buys karate belt',
'Buys uniforms like military uniform', 'Buys institutional uniform').

**The screen must use its own output as the skip list:**

```python
_already_screened = (set(_prev_raw.get('ours', {}))
                      | set(_prev_raw.get('theirs', {}))
                      | set(_prev_raw.get('unknown', {})))
todo = [(k, v) for k, v in h.items() if k not in _already_screened][:LIMIT]
```

Fixing this took `ours` from **61 to 111** and finally let `theirs`
fire at all (0 -> 151). Full pool: 865 harvested, 865 screened.

## A COMPANY BELONGS IN EXACTLY ONE BUCKET

Re-screening a company must REPLACE its old verdict, not sit beside it.
Eight companies appeared in both `ours` and `unknown` because one fetch
failed and a later one succeeded. Pop the key from every bucket first:

```python
for bucket in (ours, theirs, unknown):
    bucket.pop(k, None)
```

## A PROFILE THAT DID NOT LOAD IS NOT 'UNKNOWN'

`unknown` means 'the profile states something we do not make'. A profile
whose page did not load says nothing at all, so filing it as `unknown`
removes it from the retry list forever. Keep those in their own file:

```python
elif buys:
    unknown[k] = v
else:
    failed_fetch[k] = v   # -> g4wb_company_failed_fetch.json, retried
```

**An empty `_buys` is NOT proof the company is a poor prospect.** Live
checks showed the pages load fine (85-115 KB) and simply state no
product line - the only 'buying verbs' in them are navigation links
('Buy', 'Import').

## THE SAME COMPANY CAN HAVE TWO MEMBER IDS

go4WorldBusiness lists Al Obaidani International LLC under both
`3404127` and `3680806`. Dedupe by company NAME within each bucket,
preferring the id that is already a lead.

## PAKISTANI COMPANIES ARE SKIPPED ON PURPOSE

`company_reach.py` marks every Pakistani company `local-pakistan` -
they are local competitors or traders, not export buyers. 71 of the 111
`ours` are Pakistani, so only **40** are actionable, and 35 of those had
never been contacted.

## THE REACH LOCK CAN GO STALE

`company_reach.lock` held the PID of a process that had died, so
`acquire_lock` refused to start and the campaign hung silently. The fix
is to confirm the live PID is actually a `company_reach` before
refusing:

```python
_cmd = open('/proc/%d/cmdline' % pid, 'rb').read().decode('utf-8','replace').replace('\x00',' ')
if 'company_reach' in _cmd:
    return False
```

## THE NVIDIA SHIELD IS A USER UNIT

`systemctl is-active nvidia-shield.service` reports `inactive` because
the unit lives in `~/.config/systemd/user/`. The correct check is
`systemctl --user is-active nvidia-shield.service` - it is active,
enabled and `Linger=yes`, running 4 days, and its adaptive rate had
correctly dropped to 1 RPM after a 429.

## THREE LATENT CRASHES IN company_reach.py

**1. `log()` was called but NEVER DEFINED.** It looked correct in review
and only raised `NameError` the moment a row failed to land - which
killed the whole campaign mid-run and lost the batch. Use `print()`.

**2. New rows were written at the END of the batch.** The state file
said `'added'` while the row still sat in memory, so a kill between the
two lost that lead FOREVER - the state marked it done so it was never
retried. Write each row as soon as it is built:

```python
from leads_safe_write import add_rows
add_rows([row])
```

**3. The lock could go stale.** `company_reach.lock` held the PID of a
process that had died, so `acquire_lock` refused to start and the
campaign hung silently with an empty log. Confirm the live PID is
really a `company_reach` before refusing (see above).

**A silent hang is worse than a crash** - a crash shows a traceback, a
stale lock just produces an empty log file. After any timeout, check
the lock file and the log before assuming the campaign did nothing.

## THE REACH CAMPAIGN IS SLOW BY DESIGN

The NVIDIA shield's adaptive rate had dropped to 1 RPM after a 429, so
each company takes 1-2 minutes (it runs several LLM calls per company).
A 12-company batch needs ~25 minutes. Run it in the BACKGROUND - a
foreground call gets killed by the timeout.

## A CONFIRMED BUYER WHOSE SEARCH FAILS MUST NOT BE RETIRED

`company_reach.py` marked a company `no-match` whenever the web search
failed to find its site. For a company that had already been CONFIRMED by
the screen - it states on its own profile that it buys uniforms - that is
a transient failure, not a rejection. **20 verified buyers were retired
this way** (police uniforms, military uniforms, school uniforms).

Three fixes, all needed:

```python
def _is_confirmed_buyer(kid):
    try:
        with open('/home/ubuntu/g4wb_company_screened.json', encoding='utf-8') as f:
            sc = json.load(f)
        return kid in sc.get('ours', {})
    except Exception:
        return False
```

1. the failure path must set `retry-buyer`, not `no-match`
2. an unreachable site must set `retry-buyer`, not `no-match`
3. **the skip list must let them back in** - `if k in done: continue`
   retires them permanently, so `retry-buyer` entries have to be allowed
   through until the cap:

```python
if k in done:
    _st = done.get(k)
    _stt = _st.get('status') if isinstance(_st, dict) else _st
    if _stt == 'retry-buyer':
        if _retry_count(_st) >= 3:
            continue          # cap reached - set aside for review
    else:
        continue
```

Cap the retries at 3, then set them aside as `buyer-no-site` for a manual
look. Without a cap the campaign loops on the same company forever.

## WHY THE SEARCH FAILS FOR MANY OF THESE BUYERS

The go4WorldBusiness profile carries **no website link** - it has the
company name, country, category and the 'Buys ...' sentence, and nothing
else. So the only route to a contact is a web search.

Traced end to end for Salem Abdullah Al Qattan & Sons (Kuwait):

| step | result |
|---|---|
| `search_company` | finds `dalil-alkuwait.com`, `bizmideast.com`, `kuwaityello.com` |
| domain filters | all three pass |
| `dalil-alkuwait.com` | loads (28 KB) but is a Kuwait **business directory**, not the company - correctly rejected |
| `bizmideast.com` | behind a **challenge wall** |
| `kuwaityello.com` | an **INFO_SITE** directory listing |
| `emails_from('https://dalil-alkuwait.com')` | DOES find `kw-29@hotmail.com` |

**The filters are right; the company simply has no site of its own that
the search can reach.** This is exactly what the go4WorldBusiness
Premium membership is for - it reveals a member's contact details
directly. The JUNIOR tier allows 1 buyer inquiry per day; Premium allows
100/day.

**Do not loosen the product gate to compensate.** `litoonline.com` is a
children's formal-wear shop the directory filed under 'sportswear', and
`dalil-alkuwait.com` is a directory listing. A confirmed buyer with no
findable site is a Premium question, not a filter question.
