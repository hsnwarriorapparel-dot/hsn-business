---
name: hsn-business-hub
description: Business outreach, lead hunting, and client replies for HSN Warrior Apparels — rules, prices, quotas, tools.
version: 2.0.0
metadata:
  hermes:
    tags: [outreach, leads, whatsapp, instagram, hsn-warrior, business-hub]
---

# HSN Warrior Apparels — Complete Business Hub

## When to Use
Load for ANY task touching this business: lead hunting, cold outreach sends (WA/email/IG), client replies, price quotes, tracker updates, worker/cron maintenance, and user reports. Cold outreach to new leads is autonomous; anything involving an existing client conversation is draft-only until the user says send.

## Company Identity
- **Brand:** HSN Warrior Apparels (NEVER "Mibro International" or "Hassan Warrior" — user corrected this)
- **Owner:** HSN Bajwah
- **Location:** Sialkot Industrial Estate, Sialkot 51310, Pakistan
- **Since:** 2011
- **Products:** BJJ gis, judo/karate/taekwondo uniforms, MMA fightwear, boxing gear, Thai pads, focus mitts, shin guards, headgear, belts, hoodies, rash guards, team sportswear
- **Model:** B2B OEM/private label, low MOQ for clubs
- **Contact info for all messages:** hsnwarriorapparel@gmail.com | WhatsApp +92 337 3336381 (user corrected: 923373336381) | IG @hsnwarriorapparel

## 🔴 CRITICAL CLIENT RULES
1. **Client REPLIES = draft only.** NEVER send a reply to an existing conversation without user's explicit "send" command. Cold outreach to NEW leads stays autonomous.
2. **Verify-first protocol (mandatory):** Before ANY WhatsApp send: (1) verify chat header shows the client's exact number, (2) send, (3) verify the message text appears in THAT chat's transcript. Same principle for IG DMs and email recipients.
3. **Every lead found = send to all available channels same day:** IG follow + IG DM + email (if address exists) + WhatsApp (if number exists).
4. **Sheet discipline:** Add IG username + profile link + email + phone + profile analysis IMMEDIATELY when a profile is found. Never leave a profile's contact info uncaptured.
5. **Short professional messages** — no long paragraphs. No catalog/website links until user says they're ready (catalog/website were "not ready" as of 2026-10-13).
6. **No "free sample" offers** (user removed them). Personalize each message by name — never identical templates.
7. Personalize in client's language when needed (Google Translate for Italian/Spanish/etc. — user approved this approach for non-English clients).

## Daily Quotas (user-set)
- **16 WhatsApp DMs to NEW leads** — keep hunting profiles until 16 WA leads found AND messaged
- **25 emails daily** — every lead with an email gets one
- **All profiles found: IG follow + IG DM**
- While hunting for the 16 WA leads, any profile without WA still gets email + IG follow + DM immediately

## Price List (user-provided — EUROS)
- Jiu-Jitsu Gi (450g): €29.60
- Rash Guard: €9.50
- MMA Shorts: €9.90
- MMA Tights: €12.50
- Jiu-Jitsu Belts: €3
- Hoodies: €14.50
- Boxing Gloves Cowhide: €25.50 | Faux Leather: €19.50
- Shin Guards Cowhide: €28.50 | Faux: €22.50
- Headgear Cowhide: €24 | Faux: €19
- Thai Pads: €34.50
- Focus Mitts: €26.50
- Included with all: ✅ custom brand logo, ✅ tax-free shipping

## Tools & Infrastructure (VPS: Oracle Cloud 129.146.37.209)
- **Work browser:** Chromium snap, profile ~/work-profile-1, CDP port 9222. Launch needs Xvfb :20 or :21 + XAUTHORITY=~/.hermes/bot-desktop/Xauthority. IG + WhatsApp Business + Gmail all logged in.
- **CDP helper:** /home/ubuntu/cdp_helper.py (websocket-client, suppress_origin=True)
- **Outreach scripts:** /home/ubuntu/worker.py (queue runner; save_leads is row-targeted — never revert to full-file rewrite), /home/ubuntu/outreach.py (ig_open_profile, ig_follow, ig_dm, gmail_send, wa_send), /home/ubuntu/templates.py (message builders with correct brand/phone)
- **Tracker:** /home/ubuntu/leads.csv + /home/ubuntu/HWA_Lead_Tracker.xlsx. Schema (15 cols): Lead ID, Name, Type, IG Username, IG Profile Link, City, Country, Phone, Phone Type, Email, Website, Status, Profile Analysis, Products Needed, Notes
- **Channel send mechanics (WA / Gmail / IG):** full step-by-step in `references/outreach-channel-mechanics.md` — header-verified send?phone flow for WA, "isn't on WhatsApp" detection, phone-format validation (truncated/local-number rules), Compose-button flow for Gmail, IG follow+DM flow, batch limits (≤6 leads per terminal call), scraping contamination guard.
- **Anti-block:** sleep 3-6 min between leads in worker; 12-20s between manual sends.
- **Website:** https://hsnwarriorapparels.vercel.app (source: ~/mibro-website-v3, Vercel CLI authed as paperdate25-hash, deploy: cd /tmp/hsn-deploy && vercel deploy --prod --yes). MCP vercel token lacks scope — use CLI.
- **Catalog PDF:** /home/ubuntu/HSN_Warrior_Apparels_Catalog.pdf (built via /tmp/build_catalog.py with reportlab, compressed via gs /printer setting). 12 products, 6 pages. DO NOT send until user confirms it's final.
- **GitHub backup:** github.com/hsnwarriorapparel-dot/hsn-business (private). Nightly backup 2:00 UTC via cron 8d87b574012b (script ~/.hermes/scripts/backup-git.sh). SSH key: /home/ubuntu/.ssh/hsn_backup_key (needs IdentitiesOnly=yes in GIT_SSH_COMMAND).
- **agent-reach v1.5.0** installed (pipx → ~/.agent-reach-venv): working = web reader (curl https://r.jina.ai/URL), Exa search via `mcporter call 'exa.web_search_exa(query: "...", numResults: N)'`, yt-dlp, RSS, V2EX, Bilibili. Skill at ~/.hermes/skills/agent-reach/. Login-required channels (Twitter/Reddit/IG/FB/XHS/LinkedIn) NOT configured.
- **Exa search = primary lead-hunting tool:** search "gym kickboxing [country] WhatsApp contact instagram" → get gym websites → curl each for wa.me/ + emails + IG handles → verify on IG via browser.

## Lead Pipeline Status (as of Day 3 morning UTC)
- **142 leads in tracker** (L001-L142): ES, PT, DE, FR, IT, NL, PL, UK, BE, AT, CH
- **Day 2 final:** 17/16 WA, 43/25 emails, 37 IG — quota complete
- **Day 3 in progress:** 7/16 WA, 21/25 emails, 22 IG (Belgium, Austria, Portugal, FR/CH/UK batches done)
- **Warm/hot leads:** BJJ Aachen (follows user), Kickboxing Madrid chain, DM Fight (reseller), Gracie Barra Braga (franchise), FENRIZ Berlin (8.1K followers), SPORTS PLACE (9.6K), Loja Marcial (Tokaido distributor PT = B2B)

## Active Client Conversations (REPLIES = DRAFT ONLY!)
- **Team Duramuk (WA +351 967 734 557):** asked "Send me the prices" → SENT price list (pads+gloves focus) + apology for cross-sent messages. Note: user deleted 2 mistakenly cross-sent messages. They earlier showed their own gear work — they're a kickboxing/Muay Thai club in Lisboa (CRP Campolide), founder is World Champion, kids program. Wants: pads & gloves.
- **Scorpion Boxing Milano (WA +39 351 408 8140):** asked "Posso chiamare per informazioni sui corsi" + "Spyk Italy o e spagnol" → SENT Italian Google Translate intro. Awaiting reply.
- **Lucero Muay Thai Madrid (WA +34 633 21 53 05):** "Okay id love to see it" → SENT full price list. Awaiting reply.
- **Draco Fight Club:** replied "Gracias por comunicarte con la Academia..." — needs reading + draft.

## Watchdogs & Cron
- outreach-watchdog cron e443d3f0466b (every 30m, restarts worker if dead)
- nightly-git-backup cron 8d87b574012b (2:00 UTC)
- **Pin the absolute interpreter path in every cron/watchdog/kickoff script** — bare `python3` under cron resolves to a different, dep-less interpreter and the worker crash-loops silently all night. After any kickoff, tail the worker log within a minute: a clean "Starting" line with no traceback. A start-then-crash loop still shows as "running" to pgrep — check the log, not the process list.
- VNC for user browser access: x11vnc -display :21 -rfbport 5921 -rfbauth /home/ubuntu/.vncpassfile (password: hsn2026). Desktop shortcut "Open Agent Browser Screen" on RDP desktop.

## Template Verification Rule
Before using ANY template for a new country/lead type, render it with a real lead's data and READ the full output. Check: (1) no hardcoded country names ("delivery to Spain" went to NL/DE/FR/UK/PL clients), (2) sign-off matches lead's language context ("Gracias" went to non-Spanish clients — use "Best regards" default), (3) phone = +92 337 3336381, (4) no "free sample" claims, (5) brand = HSN Warrior Apparels only. Audit with: python3 -c "import sys; sys.path.insert(0,'/home/ubuntu'); import templates; print(templates.build_email('X','Y'))"

## Data-Integrity Rules
- **Read back every CSV write:** after writing leads.csv, re-open it and check row count + last Lead ID before reporting counts — writes have reported success while never persisting. The heredoc `python3 << 'EOF'` pattern inside terminal calls is a known way a "success" print can come from a script that wrote a different or stale file — prefer execute_code or a script file for CSV writes, and always verify on disk.
- **Never let a long-lived process own the whole leads.csv:** worker.py originally rewrote the entire file from memory; when it loaded a stale copy it wiped every lead added since. Its save is now row-targeted (re-reads disk, updates only dirty rows). Any new background writer must follow the same pattern, and if leads.csv ever reverts, restore from the git backup (`git show <newest-commit>:leads.csv`).
- **Scrape with unique temp files:** confirm each `curl -o` output exists and is non-empty before grepping — a failed curl leaves the PREVIOUS site's content in a reused temp file, attributing one gym's contacts to another. Cross-check each wa.me number's country prefix against the lead's country (+32 BE, +34 ES, +351 PT, +39 IT, +33 FR, +44 UK, +49 DE, +41 CH); a mismatch means contamination — discard the number.
- **Phone validation before any WA send:** fewer than 11 digits = truncated by the site — skip and mark for manual check; number starting with 0 = UK local format — strip the 0 and prepend 44.
- **"isn't on WhatsApp" is definitive:** when a send fails with no-composer, read the page text — WhatsApp states plainly when a number isn't registered. Mark the lead email-only; do not retry.

## Daily Runbook
Full daily procedure in `references/daily-runbook.md` — morning infra check + reply sweep (drafts only), hunt cycle per country, per-lead multi-channel sends with verification, tracker rebuild + read-back, git commit per batch, overnight kickoff checks, and the report format the user expects.

## User Preferences
- Wants EVERY action reported with full detail in chat (source, data found, what sent where)
- Wants updated Excel after every run
- Hates long messages to clients — short + professional
- Verify everything before executing; user got angry about the cross-send mistake
- User checks work in the morning (Pakistan time); overnight autonomous work is expected
- When asked "is the work done", answer with the real quota numbers first — never claim done while under target, and never report counts without re-reading the CSV
- Voice messages are Urdu-mixed-English; use faster-whisper small model via /tmp/transcribe workflow if needed
