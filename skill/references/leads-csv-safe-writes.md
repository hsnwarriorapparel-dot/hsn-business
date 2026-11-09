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

## TOOL OUTPUT REDACTS PHONE NUMBERS - DO NOT CHASE THE MASK

The terminal tool replaces phone-like strings with a masked form in its
output. `+971552997170` prints as `+971****7170`. The number on disk is
complete and correct.

**A masked number in tool output is not a defect in your code.** Three
changes were made to "fix" a mask that was only a display artifact.

Check the real value before changing anything:

```python
p = row.get('Phone') or ''
print('len=%d all_digits=%s' % (len(p), p[1:].isdigit()))
```

If `len` is right and `isdigit()` is True, the number is fine.

The same redaction applies to email-like strings in some outputs. Read
the LENGTH and a CHARACTER CHECKSUM rather than the value itself.

## A REGISTRATION NUMBER IS NOT A PHONE NUMBER

`COBRA SPORTS SDN BHD (NO. 207737-K NO. 199001016068)` produced
`+60 199001016068` - the company registration number read as a phone.
A run of digits sitting inside brackets right after `NO.`, `REG`, `VAT`,
`CRN`, `LC`, `GST` or `SSM` is an identifier, not a number to dial:

```python
_before = text[max(0, m.start() - 40):m.start()].lower()
if re.search(r'\b(no|reg(?:istration)?|vat|crn|licen[cs]e|lc|gst|'
             r'company no|reg\.?\s*no|ssm)\b[\s.:#-]{0,12}$',
             _before):
    continue
```

This one was a genuine bug and the fix is worth keeping.

## THE SEND MARKER MUST BE AT THE FRONT OF THE STATUS

The Status column is truncated at **250 characters**. The buyer-company
rows already carry a long HUNTED note, so a send marker APPENDED at the
end was cut off:

```
L5284 Supa Sportsman LLC
  Status length: 250
  ends with:    ' apply. | verified-on-own-site (email found o'
  'email sent' present: False
```

The wave's own dedupe reads the Status and looks for `email sent`. Not
finding it, it emailed the same lead again. **Three buyer companies were
sent twice on 2026-11-08** - Supa Sportsman, Cobra Sports and Apparel
Point - and one more (TOWASAN, L3372) had the same hidden marker.

Across the entire 163-send ledger history those were the ONLY
double-sends, and all of them came from this one cause.

**The marker is now PREPENDED:**

```python
update_row(lead_id, 'Status', 'COMPLETE: email sent (2026-11-08)',
           prepend=True)
```

`update_row` gained a `prepend` flag:

```python
if prepend:
    cur = (r[fi] or '').strip(' |')
    if value and value not in cur.split(' | '):
        r[fi] = (value + (' | ' + cur if cur else ''))[:250]
elif append:
    ...
```

**THE RULE: anything that must be READ BACK later goes at the FRONT of
the Status.** The end of the column is not durable.

### FINDING THE HIDDEN ONES

To find every row whose send marker was swallowed, check the LEDGER -
it is the truth about what was actually sent - against the Status
column:

```python
sent_targets = {x['target'] for x in ledger}
hidden = [r[0] for r in rows
          if len(r[status]) >= 250
          and 'email sent' not in r[status].lower()
          and r[0] in sent_targets]
```

15 rows had a full Status with no visible marker, but only 4 of them
had actually been emailed. The other 11 were never sent, so their
Status was full for an unrelated reason and they were left alone.

## A PLACEHOLDER EMAIL IS DECIDED BY ITS DOMAIN, NEVER ITS LOCAL PART

A first pass at the placeholder rule rejected any address whose local
part looked generic. That deleted **two real leads**:

- `john@johnaboxing.com` - John Andriacco Boxing, a real gym
- `info@my-club.it` - 'My Club - Palestra Padova', a real gym in Padova

Both were restored from git within minutes. **The domain is what makes an
address a placeholder.**

```python
PLACEHOLDER_EMAIL_DOMAINS = {
    'doe.com', 'doe.org', 'doe.net', 'example.com', 'example.org',
    'example.net', 'domain.com', 'email.com', 'name.com', 'test.com',
    'company.com', 'yourdomain.com', 'mydomain.com', 'yourname.com',
    'companyname.com', 'email.org', 'email.net',
}
```

A generic local part (`info@`, `your@`, `example@`, `test@`) only counts
as a placeholder when the WHOLE DOMAIN is generic too:

```python
_GENERIC_DOMAIN = re.compile(
    r'(email|domain|name|test|company|your|my|example|site|web|mail|'
    r'host|info|sales|contact)[0-9]*'
    r'([.:\-](email|domain|name|test|company|your|my|example|site|'
    r'web|mail|host|info))?\.(com|org|net|co|io|info|biz|site|online)',
    re.I)
```

`my-club.it` and `myclub.it` are REAL domains and must pass. Only
`my.com` or `my-domain.com` are placeholders.

**`company_reach.valid_email()` and `leads_safe_write.email_is_contactable()`
must agree.** They were separate implementations and drifted, which is how
a rule can reject an address in one place and accept it in another. The
shared test `test_placeholder_email.py` checks both against the same
cases and fails if they disagree.

## WHEN A ROW HAS SEVERAL ADDRESSES

`user@domain.com, nora.ermatinger@gmail.com` is not a placeholder row -
it has one placeholder and one REAL address. Remove only the placeholder
and keep the real one. A row is only deletable when EVERY address on it
is a placeholder.

## A BAD EMAIL IS CLEARED, NEVER THE ROW DROPPED

The first version of the contactability rule **skipped** any row whose
email was not usable. That looked harmless, and it was not:

- `read_rows()` returned 5 fewer rows than the file held
- `write_rows()` then wrote that shorter list back
- **5 real clubs were deleted**

They were Fight Factory Manchester, SubZone Fight Academy, Fighting AC-92,
Sportbox Berlin and Legends R Born - all real clubs with real websites and
phones. Only their scraped email was a placeholder. They were restored
from git.

**The rule: clear the FIELD, keep the ROW.** A club with a fake email is
still a club, reachable by phone and website.

```python
# read_rows()
if len(r) > ei and (r[ei] or '').strip() \
        and not email_is_contactable(r[ei]):
    r = list(r)
    r[ei] = ''
clean.append(r)

# add_rows() - same treatment
if len(r) > _ei and (r[_ei] or '').strip() \
        and not email_is_contactable(r[_ei]):
    r = list(r)
    r[_ei] = ''
    cleared += 1
keep.append(r)
```

**THE INVARIANT: `len(read_rows()) == len(csv.reader(file))`.** If the
reader hides a row, any writer that reads and writes back will delete
it. A reader that CLEARS a field keeps the two in step.

`test_clear_not_drop.py` checks this: a row with a placeholder email
survives, the address is cleared, the reader and the disk agree, and a
read-write round trip loses nothing.

## A MALFORMED EMAIL BOUNCES EVERY TIME

The scrape produced two shapes of malformed address:

```
//info@wonsbarcelona.es                 <- a URL path prefix
%e2%80%a8%e2%80%a8support@sportingcluble   <- URL-encoded zero-width spaces
```

Both bounce on every send. The guard now rejects them:

```python
if '/' in e or '%' in e or e.startswith('mailto:') or '\\' in e:
    return False
if not re.fullmatch(r'[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}', e):
    return False
```

**The fix is to take the real address from the company's OWN website**,
not to guess the domain. L1576's scraped value was
`support@sportingclubleague.com`; the real site is
`sportingclubleonardo.it` and publishes `support@sportingclubleonardo.it`.

## THE BOUNCE RATE, AND WHAT IT ACTUALLY MEANS

| Scope | Sent | Bounced | Rate |
|---|---|---|---|
| All time | 2,182 | 100 | 4.58% |
| Today only | 89 | 3 | 3.37% |

**A bounce is usually a dead MAILBOX, not a dead domain.** All three of
today's bounces were on domains that are alive (HTTP 200/301/302) and
that publish the same address on their own site:

| Lead | Address | Domain |
|---|---|---|
| KONSTANTOPOULOS TEAM | info@konstandopoulosteam.gr | alive (200) |
| Taekwondo Klub ION | ion@taekwondoion.com | alive (301) |
| Predator Gym | webmaster@predatorfightgym.hu | alive (302), MX = Google |

So the domain-level filters are right to accept them, and the bounce
handler is the mechanism that catches the rest. Both work: a bounced
lead carries BOTH the 'email sent' and the 'EMAIL FAILED' marker, the
wave builder excludes anything marked 'failed', and `_is_sent()` skips it.

**A ROLE ADDRESS ON A GOOGLE-HOSTED DOMAIN IS THE RISKY CASE.**
`predatorfightgym.hu` has `MX = SMTP.GOOGLE.COM`, and Google accepts only
real mailboxes - a `webmaster@` that was never created is rejected with
'Address not found'. The 361 role addresses on Google-hosted domains are
NOT all bad (`info@` is often a configured alias), and 68 leads carry both
markers, so the bounce handler - not a guess - is what decides.

## A DEFAULT ARGUMENT CAPTURES THE PATH AT IMPORT - THE TEST WROTE INTO THE REAL TRACKER

`safe_write_csv(rows, path=CSV, ...)` captured `CSV` when the module was
IMPORTED. A test that set `lsw.CSV = TMP` was therefore IGNORED, and the
test's round-trip write went into the REAL `leads.csv`. Six
`Placeholder Test Club` rows (L9901-L9905, L9907) ended up in the live
tracker - and because the reach campaign assigns IDs from the current
max, a real buyer (Happy Life) was pushed to L9908 with a gap at L9907.

Resolve the path AT CALL TIME:

```python
def safe_write_csv(rows, path=None, expect_gen=None):
    if path is None:
        path = CSV
```

The same fix was needed in `guarded_write_csv`.

**CHECK THE HASH, NOT JUST THE VERDICT.** The test printed
`VERDICT: PASS` while corrupting the live tracker - a passing verdict
proves the assertion held, not that the test was isolated. Verify:

```python
before = sha256(leads.csv)
run_the_test()
assert sha256(leads.csv) == before
```

Run EVERY test and compare the hash after each one; a single test that
writes to the live file is enough to plant junk.

## A PHONE WITH NO COUNTRY CODE IS NOT WHATSAPP-REACHABLE

`company_reach.py` marks a local number as
`05058986100 (local - country unconfirmed)` when no country dial code
could be matched. That number must NOT go to WhatsApp - dialling it
without a country code reaches the wrong party, and some numbers belong
to someone entirely different.

The `wa.me` route is different and safe: a `wa.me` link is by
definition a full international number, so it is always usable even when
the stored phone lacks a leading `+`.
