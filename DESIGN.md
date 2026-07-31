# Design System — ReelRecall

The single source of truth for ReelRecall's look and feel. Approved by the founder, 2026-07-31 (design review + /design-consultation). Everything the build creates — app, share extension, widget, push — must use these values. Do not deviate without founder approval.

## Product Context

- **What this is:** iOS app where you share an Instagram reel, AI writes an actionable card (title + one-line action + thumbnail), and one push per day (8:30am local) surfaces "Today's card."
- **Who it's for:** People who save short-form content intending to apply it and never revisit. The founder is the primary user.
- **Space:** Knowledge activation from social saves. Competitors (Pocket, Raindrop, Instapaper) are article readers — this is a card, not a library.
- **Project type:** Native iOS app (SwiftUI) + share extension + widget. One screen in the app ("Today's card" — D7). No tabs, no list.

## Aesthetic Direction

- **Direction:** Reference-app language — extracted by the founder via Gemini from a reference app they chose. Locked D11–D13: light mode, white background, floating white cards, purple accent, system typography. (Two assistant-proposed palettes were rejected as "horrible" — the reference extraction anchored everything.)
- **Decoration level:** Minimal. No gradients on UI surfaces, no emoji, no decorative blobs. One accent color, used sparingly.
- **Mood:** Calm, light, trustworthy. The app is a quiet daily ritual — a single card on white. Nothing shouts.
- **Signature:** Floating white cards on white with hairline borders and soft shadows; purple is the only color. Lock screen dark (iOS standard); share sheets system-style.
- **Reference artifacts:**
  - Approved mockups: `~/.gstack/projects/SavedPostIdea/designs/hero-screens-20260731/` (card-screen.html, share-flow.html, push-widget.html)
  - Motion + icon proposal (this session): `~/.gstack/projects/SavedPostIdea/designs/design-consultation-20260731/motion-icon-preview.html`

## Typography

- **Stack:** System (SF Pro on iOS). No custom fonts — platform-native, matches the reference.
- **Scale (locked, plan Pass 5):**

| Role | Size | Weight | Tracking | Line height |
|------|------|--------|----------|-------------|
| Hero (card title) | 34 | 700 | -1.2 | 1.2 |
| Section | 17 | 600 | -0.4 | 1.3 |
| Headline (app name) | 20 | 600 | -0.4 | 1.3 |
| Body | 15 | 400 | -0.2 | 1.4 |
| Caption (meta) | 13 | 400 | — | 1.3 |
| Button | 17 | 600 | -0.4 | — |
| Kicker (eyebrow) | 12 | 600 | +0.6 (uppercase) | — |

- Dynamic Type is required: layouts scale with system text sizes, hero truncates to 2 lines gracefully, thumbnails flex, share-sheet copy wraps.

## Color

- **Approach:** Restrained. One accent + neutrals. Color is rare and meaningful.
- **Core tokens (locked, plan Pass 5; tertiary a11y-corrected D18):**

| Token | Hex | Usage |
|-------|-----|-------|
| background / card | #FFFFFF | App bg, floating cards |
| hairline border | #E0E0E0 | Card outlines |
| separator | #F0F0F0 | Dividers, hairlines inside cards |
| text primary | #1C1C1E | Titles, body |
| text secondary | #6E6E73 | Meta, captions |
| text tertiary | #7A7A80 | Tertiary text (a11y-corrected from #A4A4A8 — ≈4.6:1 on white) |
| accent | #7879F1 | The only accent. Buttons, links, icon |
| on-accent | #FFFFFF | Text on accent |
| success | #30D158 | "Saved ✓" check, done states |
| placeholder | #E2E2E5 | Shimmer skeleton, empty thumbnails |

- **Dark mode:** Light-only for MVP (D19). No dark palette defined yet; revisit after demand signal.
- #A4A4A8 is allowed only for non-text decoration.

## Spacing & Shape

- **Base unit:** 4pt scale.
- **Spacing tokens:** page margin 16, card padding 16, section gaps 24, element gaps 12.
- **Radii:** cards 16, buttons 12, thumbnails 8, badges 50%.
- **Effects:** card shadow `0 2px 4px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.05)`. No gradients on UI surfaces.
- **Touch targets:** ≥44pt (thumbnails and links get extended hit areas).

## Layout

- **Approach:** One-screen app (D7). Card-is-the-screen (D6).
- **Main screen anatomy (top to bottom):** brand + date header → kicker "Today's card" → THE CARD: title (hero) → action line (body) → video thumbnail (no play badge — see Icon & Imagery) → "Open the reel" accent button (the pull-back reason is the button label) → meta row (saved age, creator) → "✓ I did this" → collapsible "What are you working on?" context field below the card (D22).
- **Settings:** gear top-right (settings, data deletion, context field). No bottom bar.
- **Share extension:** capture surface, not a home. Three-branch state machine (D8): instant "Saved ✓" ≤1s → card upgrades in place ≤4s → "Saved — your card is ready shortly" + "Open ReelRecall" handoff (D21). Cancel discards the save (D24).
- **Push (D23):** 8:30am local, `Saved 3 days ago: {title} — {action}`. Tap → card screen. Widget shows the same card (push-permission-denied fallback).
- **State table** (approved, plan Pass 2): loading = shimmer skeleton (no layout jump); empty first-run = "Share a reel from Instagram"; error = "This post is no longer available"; queue exhausted = "No cards left — share a reel to refill"; bare save = "Saved — it's in your queue."

## Motion (approved 2026-07-31, /design-consultation)

- **Approach:** Intentional. Calm everywhere, one signature moment. No bounce anywhere. Hard ceiling 400ms per moment — the app never feels slow. (The ≤4s share-sheet budget is UI state time, not animation time.)
- **Tokens:**
  - Enter (settle): `cubic-bezier(.22, 1, .36, 1)`, 300ms — fast decel, zero overshoot
  - Exit: `cubic-bezier(.4, 0, .2, 1)`, 200ms
  - Micro (state changes, checkmarks): 120–250ms
  - Move (expands, unfolds): `cubic-bezier(.45, 0, .55, 1)`, 200–250ms
  - Haptics: light on "Saved ✓", soft on card resolve (shimmer→card), medium on "✓ I did this". Haptics persist under Reduce Motion.
- **The signature moment — the resolve (share sheet, ≤4s branch):** the shimmer skeleton IS the card's frame; its lines morph into the real text in place (300ms, enter curve) + 4pt settle + soft haptic. Morph, never replace. Nothing jumps.
- **Share extension:** ① instant "Saved ✓" — check draws 250ms, scale settle, light haptic. No skeleton before the check (1s must feel instant). ② ≤4s upgrade — the resolve (above). ③ >4s handoff — stillness: 150ms text crossfade only, no spinner.
- **Card screen:** header fades 150ms, then card rises 14pt and settles 300ms (enter curve). The soft shadow tracks the lift — the only place shadow moves. Day change / new card (D15 pull-forward): overlapping crossfade, 320ms.
- **"✓ I did this" (D20):** check pops (scale .7→1, 200ms, enter curve) + medium haptic; card content greys in place (300ms, no layout shift). Applied state feeds the paywall recap (D9).
- **Context field (D22):** chevron rotates 180° (200ms), panel unfolds (250ms, move curve); text fades first so content is readable before it leaves.
- **Shimmer skeleton:** a solid white highlight bar sweeps the #F0F0F0 skeleton lines on a 1200ms loop — a moving rectangle, not a gradient (honors the no-gradient token). Ambient; not counted against the 400ms budget.
- **Reduce Motion:** no translation, scale, or height anywhere — every state change becomes a ≤200ms opacity crossfade; shimmer renders static; haptics retained.

## Icon & Imagery (approved 2026-07-31, /design-consultation)

- **App icon — "The reel frame" (D2, founder's direction):** white field, thin purple frame, the video itself inside (a reel scene), ending in a soft fade to white at the bottom. NO play triangle anywhere.
  - The scene inside is stylized artwork (a placeholder in the proposal); final icon art to be produced (founder's Gemini screenshot→tokens→art pipeline, or a designer). App Store submission needs the full 1024px export with no alpha.
  - Rule: **the play triangle is banned** — in the icon, on thumbnails, everywhere. The product's verbs are save and tick, not play.
- **Video thumbnails (D3):** the thumbnail shows the video frame with its bottom half fading into the white card (a fade mask, not a blur). No play badge. The fade is the pull-back promise: the payoff lives in the reel.
- Empty-state illustrations: none — text-first MVP (state table copy covers all empty states).

## Accessibility

- Tertiary text #7A7A80 (≥4.5:1 on white). #A4A4A8 is decoration-only.
- Dynamic Type support (see Typography).
- 44pt touch targets minimum.
- Reduce Motion: see Motion tokens.
- Light-only MVP (D19).

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-07-31 | Design direction locked: light, white bg, purple #7879F1, floating white cards, system type (D11–D13) | Founder's reference-app extraction; two assistant palettes rejected |
| 2026-07-31 | One-screen app, card anatomy, share-extension state machine, push 8:30am, trial announce+paywall, a11y fixes (D6–D24) | /plan-design-review, all founder-approved |
| 2026-07-31 | Motion: intentional, ≤400ms, shimmer→card "resolve" as the single signature moment, haptics light/soft/medium, reduce-motion = fades | /design-consultation (D1) |
| 2026-07-31 | App icon: "The reel frame" — video in a thin purple frame fading to white; play triangle banned everywhere | Founder's note, /design-consultation (D2) |
| 2026-07-31 | Thumbnails: video with bottom fade to white, no play badge | /design-consultation (D3) |

## Build hooks

- Design tasks: `~/.gstack/projects/SavedPostIdea/tasks-design-review-20260731-205752.jsonl` (T1–T8). T6 (shared token constants incl. a11y values) consumes this file directly.
- Mockups are the visual contract: `~/.gstack/projects/SavedPostIdea/designs/hero-screens-20260731/` and `.../design-consultation-20260731/motion-icon-preview.html`.
