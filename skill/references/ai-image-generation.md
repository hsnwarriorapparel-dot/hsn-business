# AI Product Image Generation (free, via the logged-in Google account)

## STATUS / usage rule (updated after the real-photo rule)
AI-generated images are FORBIDDEN for client-facing sends (WhatsApp, email, direct client requests) — the user's explicit rule. They remain usable ONLY for IG posts / website / catalog, and even there REAL factory photos (/home/ubuntu/product_photos/) are now the preferred source; use the AI pipeline when the user explicitly approves it or for gap-filling the real-photo set. When a client asks for example photos, the answer is real photos only.

## Why this path
Paid image tools and Google AI Studio's premium models (Nano Banana Pro, Gemini 3 Flash Preview) are gated; labs.google is region-blocked from the VPS. The **consumer Gemini app (gemini.google.com)** is already logged in (hsnwarriorapparel@gmail.com session in the work browser), generates images free, and has no login wall — this is the only free image pipeline that works from this VPS. AI Studio free models and ImageFX are NOT the path.

## Non-negotiable rule
All customer-facing product imagery (IG posts, website, catalog PDF) must be AI-generated professional product shots or real factory photos. The user explicitly rejected stock-style placeholder images on the website and in the first post batch — never reuse that style; if only stock/dummy images are on hand, generate new ones first.

## Procedure
1. Open (or reuse) the tab at `https://gemini.google.com/app` in the work browser. Confirm the prompt box exists (rich-textarea / .ql-editor). If a "save login info" popup or messaging-notice modal blocks it, dismiss by clicking buttons matching: Save / OK / Not now / X / Got it / Close, then svg[aria-label="Close"].
2. Click into the prompt area with CDP real mouse (Input.dispatchMouseEvent at the textarea's coordinates), then type with `Input.insertText` (ClipboardEvent paste does NOT register in this input).
3. Submit with Enter (rawKeyDown+keyUp). "Creating your image" appears in the response area.
4. **Detect completion by blob count, not by the status text disappearing** — poll `document.querySelectorAll('img[src^="blob:"]').length` every ~5s until it exceeds the pre-send count, then wait ~3s to settle. Waiting for the "Creating..." label to vanish or for a synchronous eval return both false-timeout; long async js_eval calls (base64 conversion of the blob) exceed the websocket read limit and return empty.
5. **Extract via clip screenshot, not blob fetch:** get the LAST blob img's bounding rect and `Page.captureScreenshot` with `clip` over it (format png). Fetching the blob URL and base64-converting in-page times out — don't try it.
6. After each image, navigate to `https://gemini.google.com/app` (fresh chat) and wait ~8s between generations as rate spacing. Chain N prompts by looping steps 2-6 in one script run.
7. Verify each saved file: PNG opens, reasonable size, pixel variance > ~500 (a blank/near-blank capture means the clip missed — retake). Vision tool may be unconfigured on this box; PIL variance is the working sanity check.

## Prompt style that produced the 10-image product set (keep consistent)
Template: `Professional product photograph: [product + materials + color details], on a dark slate surface, [dramatic side] studio lighting, high-end e-commerce product photography, sharp [fabric/leather] texture visible, minimalist dark background. No people, no text, no logos`
- The "No people, no text, no logos" tail is mandatory — keeps shots brandable and avoids watermark text.
- Dark slate + consistent lighting across the set = a matching feed grid look.
- Works for: gis (specify weave/GSM), gloves (leather type), shin guards, Thai pads, focus mitts, MMA shorts, rash guards, karate/judo uniforms, headgear, hoodies, belts (arrange colored belts in a fan), team wear.

## Ready-made assets
- 10 generated images live in /home/ubuntu/ig_posts/AI_*.png (gi, gloves, shin guards, Thai pads, MMA shorts, rash guard, karate+belts, judo gi, headgear, hoodie) — reuse before generating.
- /home/ubuntu/gen_batch.py = batch loop over all product prompts (edit its jobs list for new products).
- /home/ubuntu/gemini_image_gen.py = single-image CLI: `python3 gemini_image_gen.py "<prompt>" <out.png>` (note: its older wait-for-"creating"-to-vanish detection can false-timeout; gen_batch.py's blob-count detection is the reliable one).
- Generated images are ~720×400 (screen-clip of the render). For 1080×1080 IG feed: upscale/crop with PIL (LANCZOS); or request regeneration at higher detail if the clip is too soft.
