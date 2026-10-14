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
- Do NOT send via chat-row click (xdotool). Sidebar rows shift whenever chats reorder, clicks land on the wrong row, and a paste+Enter into the still-open previous chat cross-sends the message. Chat-row clicks are for READING only; the send?phone URL is the only safe send path.
- If a wrong message did land in a client chat: tell the user immediately, never silently continue.

### Phone validation before send
- wa.me link with fewer than 11 digits = truncated by the site → skip, mark for manual verification.
- Number starting with 0 (e.g. 07790…) = UK local format → strip leading 0, prepend 44.
- Country prefix must match the lead's country; mismatch = scraping contamination, discard.

## Gmail
1. Open Gmail, click the Compose BUTTON (not a compose URL hash).
2. `Page.bringToFront` first — background tabs ignore UI clicks.
3. `Input.insertText` for recipient; verify the To chip populated before continuing.
4. Click the Send button (Ctrl+Enter is unreliable). Verify via the 'Message sent' toast.
5. `recipient-not-registered` = address doesn't exist. Retry once lowercased; if it fails again, mark the email dead in the sheet and rely on other channels.

## Instagram
1. Open `https://www.instagram.com/<handle>/` — confirm the profile exists.
2. Click Follow (text "Follow") → verify it becomes "Following".
3. Click Message → wait up to 12s for the composer → paste → Enter.
4. If no Message button appears right after following, the page may need a reload — re-check before concluding the profile can't be DM'd.

## Batch discipline
- Keep batches to ≤6 leads per terminal call — larger runs hit the tool timeout and die mid-batch. When a batch IS killed by timeout, the already-completed leads in it are done — verify their state (e.g. IG profile shows "Following"), resume ONLY the unfinished ones, and never count the whole batch as failed.
- 12–20s between manual sends; the worker sleeps 3–6 min between leads (anti-block).
- After every batch, record per-lead results; re-run ONLY the unfinished leads, never redo the whole batch.
- Batch scripts can also be killed mid-run when the user sends a message mid-turn: the tool moves them to background and the batch KEEPS RUNNING — poll the returned session_id with `process(action="poll")` instead of re-running it (re-running double-sends every lead in the list).
- IG follow results: `follow=clicked` means the click fired but the button state wasn't re-read — verify on the profile page (buttons list shows "Following") before trusting the follow; `no-btn` usually means already following.
- WhatsApp send?phone re-check: the panel sometimes needs 18-22s, and after a fresh navigation `#main` can read empty on the first check — re-read once before declaring a send unverifiable.

## Worker vs interactive sends — who owns leads.csv
- The background worker (worker.py) and interactive terminal/execute_code scripts BOTH write leads.csv. worker.py holds the whole file in memory and rewrites it — if it loads a stale copy, its next save wipes every lead and status you added since its load.
- worker.py's save_leads() has been rewritten to be row-targeted (re-reads disk, updates Status only for rows it marked `_status_dirty`, appends its leads if missing). Do NOT revert it to a full-file rewrite.
- Before restarting the worker manually, `pgrep -f "python3.*worker.py"` (not bare `worker` — that matches kernel kworkers) and kill by explicit PID list.
- If leads.csv ever reverts (row count drops, statuses reset): restore from the git backup (`cd /home/ubuntu/business-backup && git show <commit>:leads.csv > /home/ubuntu/leads.csv`) — every batch is committed, so the newest `git log` entry has the freshest data.

## Scraping contact data (Exa → curl loop)
1. Exa search per country: `mcporter call 'exa.web_search_exa(query: "<sport> gym <country/city> WhatsApp contact", numResults: 10)'`.
2. `curl -sL --max-time 12 <url> -o /tmp/<unique-per-site>.html` — ALWAYS a unique temp filename per site.
3. Confirm the file exists and is non-empty BEFORE grepping — a failed curl leaves the previous site's file and cross-contaminates contacts.
4. Extract: `wa.me/NUMBER`, emails (filter asset/sentry/example/wix and .png/.jpg/.js/.webp), `instagram.com/HANDLE`.
5. Verify IG handles in the browser before first use; verify phone format per the rules above before any WA send.
