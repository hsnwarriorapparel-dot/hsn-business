# Outreach Channel Mechanics (CDP)

Step-by-step send procedures for the work browser. Always-on rules (verify-first, draft-only on replies) live in SKILL.md; this file is the mechanical depth.

## WhatsApp — the proven flow
1. Navigate CDP to `https://web.whatsapp.com/send?phone=NUMBER` (full international, digits only).
2. Wait 15–22s for the chat panel to load.
3. VERIFY: `#main` header text starts with the number → abort if it doesn't.
4. Composer selector: `div[contenteditable="true"][aria-placeholder="Type a message"]`. Focus → paste via ClipboardEvent (DataTransfer, 'text/plain') → wait ~900ms → check composer innerText length > 40 → Enter keydown.
5. VERIFY after: message text visible in the `#main` transcript of THAT chat.

### Error handling
- `no-composer` → read `document.body.innerText`. If it contains "The number +X isn't on WhatsApp." the lead is unreachable on WA: mark email-only in the sheet, never retry. Otherwise it's load timing: retry ONCE with a 22s wait.
- **"Starting chat… Cancel" with no `#main`** = WhatsApp is still creating the chat for a brand-new number — NOT an error. Wait 10–15s more and re-check for the header before concluding anything.
- Do NOT send via chat-row click (xdotool). Sidebar rows shift whenever chats reorder, clicks land on the wrong row, and a paste+Enter into the still-open previous chat cross-sends the message. Chat-row clicks are for READING only; the send?phone URL is the only safe send path.
- If a wrong message did land in a client chat: tell the user immediately, never silently continue.

### Phone validation before send
- wa.me link with fewer than 11 digits = truncated by the site → skip, mark for manual verification.
- Number starting with 0 (e.g. 07790…) = UK local format → strip leading 0, prepend 44.
- Country prefix must match the lead's country; mismatch = scraping contamination, discard.
- A client's own email signature can carry a phone from a DIFFERENT country than the gym (e.g. PT lead replying with a +971 UAE number) — use the number they provide verbatim; the country-prefix check applies to scraped site data, not to client-supplied numbers.

## Sending photos to a client (WA Web)
**NEVER attach multiple photos in one `DOM.setFileInputFiles` call.** WA Web's attach input is `multiple=false` — a multi-file array silently sends only the FIRST image (rendered to the client as a single sticker-like image) while the caption goes out as a separate text message. Send photos ONE AT A TIME:
1. For each photo: query `input[type=file]` fresh (menu may need the + button re-clicked), `DOM.setFileInputFiles` with exactly ONE path, wait ~4s for the preview.
2. Type the caption ONLY on the first photo's preview (`div[contenteditable="true"]` in the preview, before clicking send); the rest send bare.
3. Click the send button (find `[data-icon="send"]` / aria-label Send) via real CDP mouse events.
4. ~4-5s between sends.
5. **VERIFY by counting images, not by reading text**: `document.querySelectorAll('#main img')` filtered to blob/enc sources plus the count of fresh timestamps — the caption text being present proves nothing about the photos. Report the actual image count to the user.
6. Synthetic DragEvent drops do not work on WA Web (the preview never opens) — don't retry the drop path; the per-photo file-input loop is the working method.
7. If the user says a photo batch arrived wrong ("only one sticker"), re-send the full set one-by-one — WA has no un-send, so the fix is a corrected follow-up batch, and say so plainly to the client only if the user asks (an apology draft is draft-only).

## Session-login drift: re-check tabs before every wave
1. Open Gmail, click the Compose BUTTON (not a compose URL hash).
2. `Page.bringToFront` first — background tabs ignore UI clicks.
3. `Input.insertText` for recipient; verify the To chip populated before continuing.
4. Click the Send button (Ctrl+Enter is unreliable). Verify via the 'Message sent' toast.
5. `recipient-not-registered` = address doesn't exist. Retry once lowercased; if it fails again, mark the email dead in the sheet and rely on other channels.
6. **Replying to a client email:** send via gmail_send with subject `RE: <exact original subject>` — Gmail threads it under the client's message correctly.
7. **Reading a client's reply:** search with `#search/<token>`, click the thread row, then click ALL "show trimmed content" / collapsed-message ellipses BEFORE reading — until expanded, the DOM shows only our own earlier email and the reply body is hidden. The page may need `Page.bringToFront` before button clicks respond. Gmail's built-in "Suggested reply" is visible in the DOM — ignore it and write the reply yourself.
8. **Catalog requests over email:** price list goes inline in the reply; do NOT attach the catalog PDF unless the user says "attach catalog" for that specific send.

## Instagram
1. Open `https://www.instagram.com/<handle>/` — confirm the profile exists.
2. Click Follow (text "Follow") → verify it becomes "Following".
3. Click Message → wait up to 12s for the composer → paste → Enter.
4. If no Message button appears right after following, the page may need a reload — re-check before concluding the profile can't be DM'd.
5. **Hunting a lead's email from IG** (ig_email_extractor.py): read the header/bio text and click the "more" toggle to expand truncation → open the Contact-button dialog (business accounts expose email/phone there) → follow the profile's external website link and scrape it. IG renders lazily — re-read once before declaring no email. The hunt is an enhancement, never a gate: a lead with no email still gets follow + DM.

**Working IG DM send method (React-compatible, verified 2026-10-29):** synthetic JS KeyboardEvents FAIL on IG React composers (typed text stays, nothing sends, verify=NOT_FOUND). Working method = CDP `Input.dispatchMouseEvent` (click composer) + `Input.insertText` (type) + `Input.dispatchKeyEvent` rawKeyDown/keyUp Enter (send) — same pattern as outreach.py Gmail flow.
   - Open thread: profile URL → click Message button → thread opens at /direct/t/<threadID>/ → composer is last textarea/contenteditable
   - Focus composer: `Input.dispatchMouseEvent` click on composer center
   - Type: `Input.insertText` with full message text
   - Send: `Input.dispatchKeyEvent` rawKeyDown/keyUp Enter (code=Enter, keyCode=13)
   - Verify: composer empty + marker text occurrence count in body >= 1
   - Stale IG tab WS timeouts: create a NEW tab via Target.createTarget from a healthy tab's WS

**IG DM automation LIMITATION (verified 2026-10-29):** Instagram's split-view thread panel (right side of inbox) loads the conversation in a virtualized React area. CDP `js_eval` and `Input.dispatchKeyEvent` CANNOT reliably focus the composer in existing threads with auto-replies — the element exists but Runtime.evaluate returns empty or the composer is in a shadow/virtualized tree. The 'Message' button on a profile opens a NEW compose flow, not the existing thread. WORKAROUND: when CDP fails to find composer after 3 attempts, STOP burning time — manual send from the user's phone is 100% reliable and takes <30 seconds per DM.

**IG DM send protocol when automation fails:** (1) Try CDP search → click thread → find composer (max 3 attempts). (2) If NO_COMPOSER persists: STOP. Send draft reply to user with exact text. User pastes & sends from phone Instagram app. (3) After manual send, verify in inbox list that 'Unread' clears. This is the reliable path — do NOT keep retrying CDP selectors.

**Three new IG leads with auto-replies (2026-10-29):**
  - @gbnorthphoenix72 (Gracie Barra North Phoenix): auto-reply with phone +1 (480) 887-8673 and email info@gbnorthphoenix.com. Email SENT via gmail_send (proven automation). Draft follow-up: ask adult vs kids split, promise same-day quote.
  - @boxeoelrayo (Club El Rayo): Spanish auto-reply 'Hola, somos Boxeo El Rayo 🥊 ¿En qué puedo ayudarte?'. Draft follow-up in Spanish: multi-site quantities, same-day quote.
  - @udt_atlanta (United Defense Tactical): generic 'Sure, happy to see what you have'. Draft follow-up: catalog offer, low priority.
**Email automation WORKS:** gmail_send function (outreach.py) uses CDP Compose-button flow with data-hsn-compose tagging — sent email to info@gbnorthphoenix.com successfully. Use this for all email follow-ups.

## Batch discipline
- Keep batches to ≤6 leads per terminal call — larger runs hit the tool timeout and die mid-batch. When a batch IS killed by timeout, the already-completed leads in it are done — verify their state (e.g. IG profile shows "Following"), resume ONLY the unfinished ones, and never count the whole batch as failed.
- 12–20s between manual sends; the worker sleeps 3–6 min between leads (anti-block).
- After every batch, record per-lead results; re-run ONLY the unfinished leads, never redo the whole batch.
- Batch scripts can also be killed mid-run when the user sends a message mid-turn: the tool moves them to background and the batch KEEPS RUNNING — poll the returned session_id with `process(action="poll")` instead of re-running it (re-running double-sends every lead in the list).
- IG follow results: `follow=clicked` means the click fired but the button state wasn't re-read — verify on the profile page (buttons list shows "Following") before trusting the follow; `no-btn` usually means already following.
- WhatsApp send?phone re-check: the panel sometimes needs 18-22s, and after a fresh navigation `#main` can read empty on the first check — re-read once before declaring a send unverifiable.

## Mid-batch fixes: dedupe BEFORE launching, and re-read the target list after any CSV edit
- A batch script loads its target list ONCE at startup — CSV edits made while it runs (marking rows FEDERATION/DUPLICATE/skipped) are invisible to it and it keeps processing the old list, double-DMing the very rows you just blocked. When you spot spam-class targets (federations, duplicate handles) mid-batch: STOP the batch FIRST, patch the CSV, verify the filter output with a dry read, THEN relaunch. Patching the file while the batch runs fixes nothing until restart.
- Before ANY batch launch, dry-run the target selection (print count + dup check with Counter on IG handles) and require: zero duplicate handles, zero rows whose status mentions FEDERATION/DUPLICATE/skipped. Fix the filter, not just the data, so the next run can't repeat it.
- **One IG handle = one DM ever.** Gyms list their federation's site as their own, and the hunter scrapes the SAME federation handle from many lead rows (francejudo ×7, kickboxendeutschland ×3). Passing those rows through a batch spams one account repeatedly. Dedupe on the handle across ALL leads.csv rows, not just within one batch's targets, and filter federation/association domains at HUNT time (ffjudo.fr, ffboxe, fijlkam, ffkarate, britishjudo, judobund, wako, kickboxen-deutschland, trouver-un-club, kombazen, ffsavate) — federations are not client gyms.
- Handles that look like theme/asset names (e.g. "ancora_themes") are scraper contamination from template links — strip them at hunt time, never send to them.
- To find who got double-DM'd after the fact: Counter on IG Username over rows with `dm=sent` — anything >1 needs an apology decision from the user, and the handle goes on a permanent block list.

## Session-login drift: re-check tabs before every wave
- A wave sender that worked yesterday can fail every lead with `no-gmail-tab` (email) or logged-out IG: the USER browses the VPS desktop in the same browser, closes tabs, and can log out sessions without the agent noticing. Before launching ANY send wave, run a tab check first — list CDP tabs and confirm the Gmail tab title starts with "Inbox" and IG shows the feed, not a login screen. One failed tab = fix the session BEFORE the wave, not after 20 failed leads.
- Stop the wave immediately on the first `no-gmail-tab` failure — a wave that can't send marks every lead FAILED and overwrites their statuses; kill it, fix the tab, then reset those bogus FAILED statuses before relaunching.
- A closed tab reopened via the CDP `/json/new` endpoint on this Chromium opens as about:blank — create the tab then navigate it via Page.navigate; and after navigating to mail.google.com, if the title is the Google Workspace marketing page the session is LOGGED OUT (not a redirect bug) — test `accounts.google.com`: if the account chooser shows the profile with "Signed out" beneath it, the user must re-enter the password via VNC (agent never types passwords).
- WA survives this independently — check each service's login state separately; one being logged in says nothing about the others.
- A simultaneous 3-service logout after an overnight crash means the browser lost its session cookies, not that the accounts were compromised — say so plainly to the user and route them to the 3 re-login steps (WA QR scan, IG login, Gmail password). Nothing else is lost: blocked waves leave leads pending in the CSV.

## Full work-stack restart (when the user orders a clean restart of everything)
When multiple things break at once (session wipe + crashed tabs + dead processes), the user wants a FULL clean restart — never piecemeal fixes layered on the broken state. Order:
1. Kill the work browser completely: `pkill -9 -f "work-profile-1"`, then verify with `ps aux | grep -E "work-profile|apps/desktop" | grep -v grep | wc -l` — zygotes respawn, so kill remaining PIDs explicitly until the count is 0.
2. Kill the Hermes Desktop app separately (`apps/desktop/release` PIDs) — it holds the single-instance lock, and a stale multi-day instance is the usual cause of a "black/broken screen" report.
3. Relaunch the work browser on :21 with all three service URLs as launch arguments (WA, IG, Gmail). Verify CDP 9222 answers `/json/version` AND that all three tabs exist before touching anything else.
4. Check each login state SEPARATELY (the three are wiped independently, often all at once after a night crash): WA QR screen = user must scan; IG login page = user logs in via VNC; Gmail marketing-page redirect = logged out.
5. Stage the login screens for the user: bring the WA tab to front and capture a FRESH QR via CDP screenshot cropped to the QR region, delivered at that moment (QRs expire ~1 min — re-capture on "refresh"). For Gmail, navigating straight to accounts.google.com from CDP can 401 (bot detection on the driven session) — use mail.google.com and let it bounce to the sign-in chooser instead.
6. Verify the services a session wipe does NOT touch before declaring anything dead: cron scheduler (ticker_heartbeat fresh), VNC 5921, csv_guard crontab, CDP.
7. Never relaunch send waves until the user confirms logins; report which queue waits on which login.
8. **When the user's instruction is a login-free browser** ("open without CDP / no automation"): kill Chromium, relaunch the work profile WITHOUT `--remote-debugging-port` (a fresh `manual-profile` is NOT what they want — they mean the real work profile), open the three login URLs, and drive nothing. Verify 0 CDP listeners + 0 remote-debugging flags with ss/ps before telling the user it's clean. After the user finishes logging in, relaunching the same profile WITH CDP preserves those sessions (cookies survive restart) — confirm the chat list loads before the first send.
9. **Telegram voice messages** (Urdu-mixed) arrive as .ogg in ~/.hermes/cache/audio/ — transcribe with faster-whisper small model after `ffmpeg -i in.ogg -ar 16000 -ac 1 /tmp/vm.wav`; if it crashes on `av.open(... metadata_errors=)`, pin `pip install "av==15.1.0"` (no ARM wheels exist for older av).

## Missed cron fire after a scheduler restart
- A gateway/scheduler restart AT the exact scheduled fire time loses that run: `next_run_at` jumps a full day ahead and no output file appears for today. Recover: `ls /home/ubuntu/.hermes/cron/output/<job_id>/` — no file for today means fire it manually with `cronjob action=run`.
- If action=run answers "Job is already running", a scheduler tick IS executing it — do not re-fire; wait for the delivery.
- A scheduler restart does not disable jobs — only the fire that landed inside the restart window is lost.

## Worker vs interactive sends — who owns leads.csv
- The background worker (worker.py) and interactive terminal/execute_code scripts BOTH write leads.csv. worker.py holds the whole file in memory and rewrites it — if it loads a stale copy, its next save wipes every lead and status you added since its load.
- worker.py's save_leads() has been rewritten to be row-targeted (re-reads disk, updates Status only for rows it marked `_status_dirty`, appends its leads if missing). Do NOT revert it to a full-file rewrite.
- **CSV writes must be temp-write + verify + atomic replace** (/home/ubuntu/safe_csv_update.py): write to a tempfile, re-read it, assert the row count matches, THEN os.replace onto leads.csv. Naive open(CSV,'w') scripts have truncated the file to 0 bytes — a plain w-mode open empties the file the moment the handle is created, so ANY crash between open and writerows loses everything.
- **Never commit an empty leads.csv** — the git repo has a pre-commit hook that BLOCKS commits when the staged leads.csv has <300 lines. If a commit is blocked by the hook, that is the guard working: fix the CSV (restore from git history) instead of bypassing the hook.
- **Recovery recipe when leads.csv is 0 bytes:** walk `git log` for the newest commit where `git show <commit>:leads.csv | wc -l` > 300, restore from that commit, then re-apply lost updates with safe_csv_update.py. Both /home/ubuntu/leads.csv AND business-backup/leads.csv can be zeroed by a bad copy+commit — check BOTH before restoring.
- Before restarting the worker manually, `pgrep -f "python3.*worker.py"` (not bare `worker` — that matches kernel kworkers) and kill by explicit PID list. `pgrep -f <pattern>` ALSO matches the agent's own shell wrapper that contains the pattern text — verify candidates with `ps aux | grep <pattern> | grep -v grep` before killing, or you SIGTERM your own shell and lose the turn's output.
- If leads.csv ever reverts (row count drops, statuses reset): restore from the git backup (`cd /home/ubuntu/business-backup && git show <commit>:leads.csv > /home/ubuntu/leads.csv`) — every batch is committed, so the newest `git log` entry has the freshest data.

## Scraping contact data (Exa → curl loop)
1. Exa search per country: `mcporter call 'exa.web_search_exa(query: "<sport> gym <country/city> WhatsApp contact", numResults: 10)'`.
2. `curl -sL --max-time 12 <url> -o /tmp/<unique-per-site>.html` — ALWAYS a unique temp filename per site.
3. Confirm the file exists and is non-empty BEFORE grepping — a failed curl leaves the previous site's file and cross-contaminates contacts.
4. Extract: `wa.me/NUMBER`, emails (filter asset/sentry/example/wix patterns AND obvious placeholders like `deine@email`, plus .png/.jpg/.js/.webp), `instagram.com/HANDLE`.
5. Verify IG handles in the browser before first use; verify phone format per the rules above before any WA send.
6. **Dedupe phone numbers across the whole CSV before sending** — the same gym owner often runs multiple sites with one WA number; two leads sharing a number means one contact, not two sends.
7. **Exa returning empty is usually transient rate-limiting, not a broken tool** — wait 20–25s and retry with a simpler query before concluding anything; only pivot after the retry also fails.
8. **IG header/bio text almost never contains the WA number** (external links live in the profile link field, not the bio text) — don't burn cycles scraping bios for phones; get numbers from the gym websites.
9. **If a whole region's sites fail DNS/connect (HTTP 000), pivot to other countries** — connectivity failures are selective and transient; hammering dead endpoints wastes the hunt window while reachable countries still fill the quota.

## Related
- AI product-image generation (Gemini app procedure, prompts, extraction, verification): `references/ai-image-generation.md`
- Daily operating procedure + report format: `references/daily-runbook.md`
- Full work-stack restart and missed-cron recovery procedures are in this file (see the restart + cron sections above).
