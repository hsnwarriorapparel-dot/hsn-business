---
name: hsn-business-hub
description: HSN Warrior Apparels complete business context — outreach pipeline, client rules, prices, tools, and daily quotas. Load for ANY business/outreach/client work.
version: 2.0.0
metadata:
  hermes:
    tags: [outreach, leads, whatsapp, instagram, hsn-warrior, business-hub]
---

# HSN Warrior Apparels — Complete Business Hub

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
2. **Verify-first protocol (locked in after 2026-10-13 mistake):** Before ANY WhatsApp send: (1) verify chat header shows the client's exact number, (2) send, (3) verify the message text appears in THAT chat's transcript. Same principle for IG DMs and email recipients.
3. **Every lead found = send to all available channels same day:** IG follow + IG DM + email (if address exists) + WhatsApp (if number exists).
4. **Sheet discipline:** Add IG username + profile link + email + phone + profile analysis IMMEDIATELY when a profile is found. Never leave a profile's contact info uncaptured.
5. **Short professional messages** — no long paragraphs. No catalog/website links until user says they're ready (catalog/website were "not ready" as of 2026-10-13).
6. **No "free sample" offers** (user removed them). Personalize each message by name — never identical templates.
7. Personalize in client's language when needed (Google Translate for Italian/Spanish/etc. — user approved this approach for non-English clients).

## Daily Quotas (user-set, 2026-10-13)
- **16 WhatsApp DMs to NEW leads** — keep hunting profiles until 16 WA leads found AND messaged
- **25 emails daily** — every lead with an email gets one
- **All profiles found: IG follow + IG DM**
- While hunting for the 16 WA leads, any profile without WA still gets email + IG follow + DM immediately

## Price List (user-provided, 2026-10-13 — EUROS)
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
- **Outreach scripts:** /home/ubuntu/worker.py (queue runner), /home/ubuntu/outreach.py (ig_open_profile, ig_follow, ig_dm, gmail_send, wa_send), /home/ubuntu/templates.py (message builders with correct brand/phone)
- **Tracker:** /home/ubuntu/leads.csv + /home/ubuntu/HWA_Lead_Tracker.xlsx. Schema (15 cols): Lead ID, Name, Type, IG Username, IG Profile Link, City, Country, Phone, Phone Type, Email, Website, Status, Profile Analysis, Products Needed, Notes
- **Gmail via CDP:** click Compose BUTTON (not URL hash) → Page.bringToFront required (background tabs ignore UI clicks) → Input.insertText for recipient → click Send button (Ctrl+Enter fails) → verify via 'Message sent' toast + drafts count. Email addresses with capitals may need lowercasing (Usera Fight Club case).
- **WhatsApp via CDP:** navigate to web.whatsapp.com/send?phone=NUMBER, wait 15s+. Composer = div[contenteditable="true"][aria-placeholder="Type a message"]. Paste via ClipboardEvent, send via Enter keydown. For chats already in list: click the chat ROW via xdotool (desktop coords = page coords + 152 for window offset: 65 window Y + 87 chrome UI), verify #main header shows the number FIRST.
- **IG DM:** open profile → click Message → wait up to 12s for composer → paste → Enter.
- **Anti-block:** sleep 3-6 min between leads in worker; 12-20s between manual sends.
- **Website:** https://hsnwarriorapparels.vercel.app (source: ~/mibro-website-v3, Vercel CLI authed as paperdate25-hash, deploy: cd /tmp/hsn-deploy && vercel deploy --prod --yes). MCP vercel token lacks scope — use CLI.
- **Catalog PDF:** /home/ubuntu/HSN_Warrior_Apparels_Catalog.pdf (built via /tmp/build_catalog.py with reportlab, compressed via gs /printer setting). 12 products, 6 pages. DO NOT send until user confirms it's final.
- **GitHub backup:** github.com/hsnwarriorapparel-dot/hsn-business (private). Nightly backup 2:00 UTC via cron 8d87b574012b (script ~/.hermes/scripts/backup-git.sh). SSH key: /home/ubuntu/.ssh/hsn_backup_key (needs IdentitiesOnly=yes in GIT_SSH_COMMAND).
- **agent-reach v1.5.0** installed (pipx → ~/.agent-reach-venv): working = web reader (curl https://r.jina.ai/URL), Exa search via `mcporter call 'exa.web_search_exa(query: "...", numResults: N)'`, yt-dlp, RSS, V2EX, Bilibili. Skill at ~/.hermes/skills/agent-reach/. Login-required channels (Twitter/Reddit/IG/FB/XHS/LinkedIn) NOT configured.
- **Exa search = primary lead-hunting tool:** search "gym kickboxing [country] WhatsApp contact instagram" → get gym websites → curl each for wa.me/ + emails + IG handles → verify on IG via browser.

## Lead Pipeline Status (as of 2026-10-13 ~16:00 UTC)
- **~89 leads in tracker** (L001-L089): Spain, Portugal, Germany, France, Italy, Netherlands, Sweden, Poland
- **Grand totals:** 58+ IG follows, 61+ IG DMs, 42+ emails, 25+ WhatsApp sent
- **Day 2 (Oct 13) progress: 8/16 WA sent** (Mugendo Eixample, HardiFit, Fight Culture, Porradaria, Lucero Madrid, Muay Thai Kassel, Muniz Boxing, Scorpion Boxing), 15 emails, 18 IG
- **7 Poland leads (L083-L089) just added** — emails sending in background
- **Warm/hot leads:** BJJ Aachen (follows user), Kickboxing Madrid chain, DM Fight (reseller), Gracie Barra Braga (franchise), FENRIZ Berlin (8.1K followers), SPORTS PLACE (9.6K), Loja Marcial (Tokaido distributor PT = B2B)

## Active Client Conversations (REPLIES = DRAFT ONLY!)
- **Team Duramuk (WA +351 967 734 557):** asked "Send me the prices" → SENT price list (pads+gloves focus) + apology for cross-sent messages. Note: user deleted 2 mistakenly cross-sent messages. They earlier showed their own gear work — they're a kickboxing/Muay Thai club in Lisboa (CRP Campolide), founder is World Champion, kids program. Wants: pads & gloves.
- **Scorpion Boxing Milano (WA +39 351 408 8140):** asked "Posso chiamare per informazioni sui corsi" + "Spyk Italy o e spagnol" → SENT Italian Google Translate intro. Awaiting reply.
- **Lucero Muay Thai Madrid (WA +34 633 21 53 05):** "Okay id love to see it" → SENT full price list. Awaiting reply.
- **Draco Fight Club:** replied "Gracias por comunicarte con la Academia..." — needs reading + draft.
- **2026-10-13 incident:** 3 messages cross-sent to Duramuk's chat (Lucero's list + Scorpion's Italian msg landed in Duramuk). User deleted them. Apology sent. Cause: WA chat-click didn't switch chats before send; fix = verify header before + transcript after every send.

## Watchdogs & Cron
- outreach-watchdog cron e443d3f0466b (every 30m, restarts worker if dead)
- nightly-git-backup cron 8d87b574012b (2:00 UTC)
- VNC for user browser access: x11vnc -display :21 -rfbport 5921 -rfbauth /home/ubuntu/.vncpassfile (password: hsn2026). Desktop shortcut "Open Agent Browser Screen" on RDP desktop.

## User Preferences
- Wants EVERY action reported with full detail in chat (source, data found, what sent where)
- Wants updated Excel after every run
- Hates long messages to clients — short + professional
- Verify everything before executing; user got angry about the cross-send mistake
- User checks work in the morning (Pakistan time); overnight autonomous work is expected
- Voice messages are Urdu-mixed-English; use faster-whisper small model via /tmp/transcribe workflow if needed
