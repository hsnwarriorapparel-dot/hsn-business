# Daily Outreach Runbook

PKT = UTC+5 (user's timezone; e.g. 1:00 AM PKT kickoff = 20:00 UTC).

## Morning (user wakes ~6 AM PKT)
1. **Infrastructure first, honestly:** `pgrep -f worker.py` + `tail /home/ubuntu/worker_stdout.txt`. Look for import errors or repeated tracebacks = overnight crash loop. If it crashed: fix it, then say so plainly in the morning report — never bury a failed night.
2. **Client-reply sweep (DRAFT ONLY — never send):**
   - WA: scan the chat list for unread badges; open every chat with new inbound messages.
   - IG: direct inbox + the Requests folder (replies from non-followers land there).
   - Gmail: inbox scan; ignore auto-replies.
3. Draft replies in the chat for the user's approval. One draft per client, short and professional, client's language if needed.

## Hunt cycle — repeat until daily quota met
1. Pick the next country/city; Exa search for gyms with WhatsApp contact.
2. Curl each result site → extract WA / email / IG (see `references/outreach-channel-mechanics.md`).
3. Add leads to leads.csv IMMEDIATELY with every column filled: IG username, profile link, email, phone, website, profile analysis, products needed. Write via execute_code or a script file — NOT a `python3 << 'EOF'` heredoc — and read the file back (row count + last Lead ID) before moving on.
4. Send per lead on every channel they have: WA (verified flow) + email + IG follow + IG DM. Batches ≤6 leads per call.
5. Update statuses in leads.csv; rebuild HWA_Lead_Tracker.xlsx; READ BACK the CSV (row count + last Lead ID) to confirm the write persisted.
6. Commit + push to GitHub after every batch — this is also the recovery point if leads.csv ever gets clobbered.
7. Cross-check the day's counts against the CSV before reporting quotas — if the on-disk count disagrees with what you tracked, the file was clobbered: restore from git, then reconcile statuses before telling the user any number.

## Quotas (reset daily)
- 16 WhatsApp DMs / 25 emails / every found lead gets IG follow + DM.
- Email quota completing early does NOT stop the WA hunt: keep finding WA-verified leads until 16 WA sends, contacting every profile found along the way on whatever channels it has.

## Overnight kickoff (when user sets a start time)
- Schedule with the ABSOLUTE interpreter path that has the dependencies — bare `python3` in a cron/kickoff context resolves to a dep-less interpreter and crash-loops silently.
- Within a minute of kickoff, tail the worker log: a clean "Starting" line with no traceback. A start-then-crash process still reads as "running" to pgrep — check the log, not the process list.

## Report format (user wants every action detailed)
- Per lead: where found, what contact data extracted, which channels sent, verification result for each send.
- Morning report: honest overnight accounting (ran / failed / fixed), quota table (done vs target), WA send list with countries, new-lead count, and any rejected contacts with the reason (not on WhatsApp, dead email, contaminated number).
