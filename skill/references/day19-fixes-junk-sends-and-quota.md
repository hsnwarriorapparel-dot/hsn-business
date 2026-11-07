# Day-19 fixes (2026-11-02): tracker contamination + daily quota across senders

## 1. Junk-send root cause
`process_leads.py` used to split the raw `emails` scrape cell on commas and write
ONE TRACKER ROW PER ADDRESS. The engine cell mixes a real address with telemetry
noise (`<32hex>@sentry.wixpress.com`, `@sentry-next.wixpress.com`, `@sentry.io`,
`@example.com`). The 09:00 system-cron (`daily_automation_full.py` ->
`send_emails_batch`) read that tracker and emailed the junk.

**Damage done on 2026-11-02:** 50 emails sent by the 09:00 cron, of which ~46 went
to sentry/wixpress telemetry addresses, 2 were duplicate re-sends of leads already
emailed on 2026-10-29 (Parabellum Boxing, Warrior Boxing Gym), and 2 reached real
gym addresses. Gmail ground truth: `in:sent after:2026/11/02` = 50 conversations.

**FIX (applied):** `process_leads.py` now runs every cell through
`gmaps_daily_scrape.clean_email()` (rejects sentry/wixpress/placeholder/hash/
third-party domains, scores the rest against the lead's own site + name) and keeps
ONE real address per lead. It also drops any address already marked sent/failed in
`leads.csv`. Tracker: 273 rows / 127 junk -> 53 rows / 0 junk, 31 clean
READY_TO_SEND, 0 overlap with the Day-19 wave.

**FIX (applied):** the 09:00 path's send steps (email / IG / WA) are now DISABLED in
`daily_automation_full.py`. It only harvests. Never re-enable sends there without
the QA chain in front.

## 2. Daily email quota must be counted across EVERY sender
The user's hard limit is 100 cold emails per calendar day. It applies to the wave
AND to any other sender, junk or not.

`day19_wave_runner.py` now has a quota guard:
- reads `/home/ubuntu/dayNN_quota_state.json` (`daily_email_quota`,
  `emails_sent_today_before_wave`)
- counts today's `email sent` markers in leads.csv
- allowance = quota - MAX(pre-wave count, live count)
- trims the wave to the allowance, or exits if the allowance is 0

**Before firing a wave:** verify the real Gmail count
(`in:sent after:YYYY/MM/DD` -> the "1-50 of N Conversations" header) and write that
number into the quota-state file. On 2026-11-02 the allowance was 50, so the
Day-19 wave was trimmed 100 -> 50.

## 3. WA session
Still QR-dead since 2026-10-24 (day 10+). WA sends stay at 0 until the user
re-links WhatsApp Web from phone/VNC. Check with a CDP probe for "Scan to log in"
vs `#pane-side`; never send into a QR screen. Fresh QR is saved to
`/home/ubuntu/wa_qr_dayNN.png`.

## 4. Copy rules reminder
The 09:00 path wrote `Hi <name>,` greetings, which are banned by
`spam-word-checker` (no greeting prefix before the first name). The dayNN wave
path uses `templates.py`, which already complies. Keep sends on the wave path.
