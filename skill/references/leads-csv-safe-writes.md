# leads.csv writes must be locked (2026-11-07)

## THE HEADER ROW MUST NEVER BE FILTERED OUT

`leads.csv` has a header row:

```
Lead ID,Name,Type,IG Username,...,Email,Website,...
```

The header's Email cell contains the **literal text `Email`**. Any filter
that runs over the rows and asks 'is this a usable email address?' will
read `Email` as an address, decide it is undeliverable, and **delete the
header**. Every later read is then off by one and `rows[0]` is a data
row.

This actually happened - the file lost its header three times during one
cleanup, and the symptom was confusing: `write_rows()` looked correct,
the file was the right byte length, and the header still appeared to be
there - until you compared the reader's row count with `csv.reader`'s.

**The rule: always skip index 0.** In `read_rows()`:

```python
for i, r in enumerate(rows):
    if i == 0:
        keep.append(r); continue
```

And `write_rows()` refuses to write at all without a header:

```python
if not rows or not rows[0] or rows[0][0] != 'Lead ID':
    raise ValueError('refusing to write leads.csv without a header row')
```

## THE EMAIL FILTER LIVES IN THE READER, NOT THE WRITER

A lead's email must be something a buyer would REPLY to. These local
parts are forms, privacy pages and platform system addresses:

```
privacy@  no-reply@  noreply@  donotreply@  postmaster@  abuse@
hostmaster@  mailer-daemon@  sentry@  autoreply@
```

And these domains are form services, never a buyer:

```
wixpress.com  sentry.io  formsubmit.co  formspree.io  web3forms.com
googleapis.com  amazonaws.com  mailchimp.com  list-manage.com
```

**ONLY** those. `support@`, `webmaster@`, `sales@` and `enquiry@` are
real business addresses - 33 existing club leads carry `support@` and
have already been emailed successfully. A test that treats `support@` as
junk will delete live leads.

The filter must live in `read_rows()`, not in the writer. A writer-only
filter is applied to `new_rows`, but `write_rows()` then writes the
WHOLE list including any junk already on disk, so the junk comes right
back. Putting the filter in the reader means every caller - every
funnel, every tracker, every writer - sees the same clean list, and the
next write drops the junk permanently.

**The invariant to check: `len(read_rows()) == len(csv.reader(file))`.**
If they differ, the reader is filtering (good) or something is dropping
rows (bad). After a cleanup they must be equal, because the file on disk
is then written from the reader's own clean view.

## THE BOM AND THE LINE ENDINGS

The file carries CRLF line endings and may carry a UTF-8 BOM.
`read_rows()` opens with `encoding='utf-8-sig'` so the BOM is stripped;
`write_rows()` opens with plain `utf-8`. That is fine - reading with
`utf-8-sig` on a file without a BOM is harmless.

But if you read the file with plain `utf-8` and the BOM is present, the
first field name becomes `\ufeffLead ID` and a check like
`rows[0][0] == 'Lead ID'` fails for a reason that has nothing to do with
the data. Always use `leads_safe_write.read_rows()` rather than opening
the CSV yourself.

## NEVER MUTATE `leads_safe_write.CSV` IN A TEST

`CSV` is a module global. A test that points it at a scratch file and
then forgets to restore it leaves the module writing to the scratch path
while the live file stays stale - which looks exactly like the filter
not working. Reset it:

```python
lsw.CSV = '/home/ubuntu/leads.csv'   # always, before the real write
```

## THE BUG

Every script used to do this:

```python
rows = list(csv.reader(open('leads.csv')))   # read ONCE
... 20 minutes of work, adding rows ...
csv.writer(f).writerows(rows)                 # write the WHOLE stale copy
os.replace(tmp, 'leads.csv')
```

If ANYTHING else wrote leads.csv in between - the wave sending a lead, the
ammo hunt appending, another reacher adding a row - that newer work was
silently DESTROYED when the stale copy was written back.

A delayed background-process notification showed it happening: a 5,273-row
write landing on top of the merged 5,140-row file. The run that produced it
was finished hours earlier; its write had simply not been noticed.

## THE FIX - `/home/ubuntu/leads_safe_write.py`

```python
from leads_safe_write import add_rows, update_row, safe_write_csv

add_rows([row1, row2])                  # append, re-reading at write time
update_row('L1234', 'Status', 'marker', append=True)
safe_write_csv(rows, '/home/ubuntu/leads.csv')
```

- `add_rows()` re-reads leads.csv at WRITE time, so it always sees the
  current file, appends, writes, then verifies the row count.
- `acquire()` / `release()` take an exclusive lock on
  `/home/ubuntu/leads.csv.lock`. A stale lock (owner pid gone) is reclaimed.
- `update_row(..., append=True)` APPENDS to the Status marker list instead
  of replacing it, and never adds the same marker twice.
- `safe_write_csv(rows, path)` is the atomic+locked write for scripts that
  must rewrite the whole file.

## EVERY LIVE WRITER NOW USES IT

```
day24_build_wave.py      day24_ig_hunt.py        day24_ig_hunt_backlog.py
day24_ig_pass.py         day24_reply_sweep.py    day24_bounce_mark.py
day24_chain_pitch.py     day24_followup.py       gmaps_daily_scrape.py
day24_wave_runner.py     (update_status -> update_row)
buyer_reach.py           company_reach.py        (add_rows)
```

Older `dayNN_*` scripts (day11-day23) still use the old pattern, but they are
not run by the current pipeline. They become a problem the moment one of
them is re-enabled - use `safe_write_csv` when that happens.

## PROOF

`test_safe_write.py` (on a copy) and `test_concurrent_live.py` (on the REAL
file):

```
OLD WAY  -> rows: 5141 | concurrent row survived: False   <- LOST
NEW WAY  -> rows: 5143 | concurrent survived: True | my row present: True

3 concurrent writers, 15 rows: 15/15 survived, 0 errors
```

## A STALE PROCESS IS THE HARD CASE

A process that started BEFORE this module existed still has the old
read-once/write-whole-file code in memory. Locking does not help it - it
never takes the lock. It can still clobber the file at the end of a long
run. This actually happened: a delayed run notification reported "leads.csv
now 5272 rows" - a stale write landing on top of the merged 5,140-row file.

### THE SELF-HEALING FIX - no call-site changes needed

`safe_write_csv(rows, path)` now compares the caller's copy against the
LIVE file under the lock:

```
if the live file has rows the caller's copy does NOT have
    -> the caller read the file before someone else wrote to it
    -> MERGE the missing rows in instead of writing the stale copy
```

The caller's own changes are preserved AND the newer rows survive. No call
site has to pass a generation number, so no writer can forget to.

### ALSO: an explicit generation guard

`current_generation()` / `bump_generation()` track a counter in
`/home/ubuntu/leads.csv.generation`. `safe_write_csv(..., expect_gen=N)`
refuses the write outright if the generation moved since the caller read
the file. `guarded_write_csv()` is the same idea for whole-file writes.
The self-healing merge is the default; the generation guard is the explicit
opt-in.

### PROOF

```
test_stale_write.py:
  rows at start                     : 5143
  after the concurrent writer       : 5147
  STALE COPY DETECTED - 3 newer row(s) would have been lost; merging them in
  after the stale write             : 5147
  newer rows that survived          : 3 / 3
  VERDICT: PASS - the stale write did NOT destroy the newer rows
```

## THE DEDUPE - MERGE, NEVER DELETE

The tracker had **96 duplicate groups** (5,272 -> 5,140 rows). The same lead
was hunted repeatedly - `warriorsgymdub` existed on 3 rows, each with its own
outreach history.

**Deleting the duplicates lost markers.** The Status column is capped at 250
chars, so merging markers overflows and truncates the END.

Correct approach: pick the primary row (most outreach markers), append the
other rows' markers to its Status, and move anything that does not fit into
**Notes** (unbounded). Verified afterwards: **all 1,115 unique touchpoints
preserved, 0 lost.** The 7 that looked lost were the *identical* marker
recorded on two rows - correctly collapsed.

Count TOUCHES, not rows, when verifying: a per-row count makes a correct
merge look like data loss.
