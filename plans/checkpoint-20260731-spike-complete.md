---
status: in-progress
branch: unknown (not a git repo)
timestamp: 2026-07-31T20:02:00-07:00
session_duration_s: 15461
files_modified:
  - eval/spike.py
  - eval/transcribe.py
  - eval/test_classifier.py
  - eval/reels.txt
  - eval/README.md
  - eval/grades-20260731-1135.md
  - eval/transcribes-20260731-1148.md
  - eval/transcribes-pullback-20260731-1153.md
  - docs/survey-posts.md
  - docs/validations/2026-07-31-saved-post-organizer-validation.md
  - TODOS.md
  - ~/.gstack/projects/SavedPostIdea/d.desmaanzephyll-unknown-design-20260731-172742.md
---

## Working on: ReelRecall MVP — spike complete, next: design review → motion demo → waitlist

### Summary

The engineering review was finished and the pre-build ingest spike (G2) was
completed end to end on the founder's real content. Extraction works 17/17,
caption-only cards work for resource reels, and the audio path (download →
transcribe → card) is proven 7/7 for talking-head reels. The load-bearing risk
is resolved: we know how to build the card pipeline. Next session: run
/plan-design-review to lock the hero screens, then the founder builds a motion
graphics demo + promo reels + email waitlist to test demand.

### Decisions Made

- **Transcription is now MVP-CRITICAL** (was stretch). Founder graded caption-only
  cards 0/7 usable on talking-head reels: "the caption is a teaser, the advice is
  spoken." Hybrid pipeline: caption for rich captions, audio for talking heads.
- **Card prompt v3 rules** (in eval/spike.py CARD_SYSTEM): name the actual thing,
  ban vague verbs (bookmark/remember/consider), ONE clear CTA under 20 words,
  ignore engagement bait (comment X/DM/link in bio), and the founder's PULL-BACK
  rule: end with a reason to reopen the reel (the card is a memory trigger, not
  the full article). This raised would-use from 1/7 to ~2.5/7+.
- **Model stack for the spike**: DeepSeek (deepseek-v4-flash, OpenAI-compatible,
  `https://api.deepseek.com/chat/completions`, key = DEEPSEEK_API_KEY) for cards;
  whisper-cpp (local, free, ggml-base.bin) for transcription; yt-dlp (updated to
  2026.07.04 — the 4-month-old version fails on Instagram) + ffmpeg for audio.
- **Production notes from the spike**: transcription exceeds the 150s Edge
  Function cap → background worker required. yt-dlp is version-fragile →
  embed-page parse or pinned+updated yt-dlp. whisper base mishears names
  (Cloud Code/Claude Code, Glyph/Glif) → upgrade model in production.
- **Carousels**: not bare saves — caption + first slide as hook (og:image already
  harvested). OCR of first-slide text is spike-gated (DeepSeek is text-only).
- Other locked decisions (from eng review): 3-day trial from first saved card,
  50-save cap, hard paywall; RevenueCat + reconcile-on-ingest entitlement gate;
  linkIdentity auth; per-hop SSRF redirect validation + CDN allowlist; rule-based
  low-info classifier; per-user TZ push scheduling; day-1 cold-start bare-save card;
  push permission asked after first card. T14 (push-vs-save A/B) is OBSOLETE.
- **Next-phase plan (founder's choice)**: design lock → motion-graphics demo →
  promo reels + landing page + email waitlist → waitlist signups feed the
  concierge test (the real go/no-go; interest ≠ engagement). Build starts after
  demand signal, ~1-2 weeks later than the original in-parallel plan.

### Remaining Work

1. Run /plan-design-review to lock the 3 hero screens (share flow, card, daily
   push) — everything downstream depends on it. The demo needs only these 3.
2. Founder: build the motion-graphics demo using REAL cards from the spike
   (eval/transcribes-pullback-*.md has the v3 cards).
3. Founder: create promo reels + landing page with email signup (landing page
   scaffold: Supabase table + one form — I build it).
4. Wire every waitlist signup into the concierge test (hand-written cards at +3
   days) — signups alone are NOT the go/no-go; engagement with cards is.
5. Reddit survey posts: r/productivity blocked 30 days (new account); post
   r/datacurator now; r/productivity after account ages (~Week 4, aligns with
   TestFlight recruiting). Drafts in docs/survey-posts.md (question-format
   version the founder prefers).
6. Build (after demand signal): 3 lanes — eval/ (seeded), supabase/ (ingest with
   per-hop SSRF + dedupe + classifier + queue + entitlement + audio worker),
   ios/ (SwiftUI, linkIdentity, widget, paywall). Tasks: T1-T16 (CEO) + T17-T27
   (eng review) in tasks-*.jsonl. T14 obsolete.
7. Founder needs to re-grade the v3 pull-back cards (7 audio cards) — last open
   question from the spike (graded 2.5 pre-pull-back).

### Notes

- DEEPSEEK_API_KEY is the founder's key (pasted in chat 2026-07-31). FOUNDER
  DECLINED adding it to ~/.zshrc (2026-07-31) — do not re-suggest. Pass it per
  run as an env var (as the harness expects). Consider rotation if the
  transcript leaves the machine.
- Harness run: `cd /Users/d.desmaanzephyll/Documents/SavedPostIdea && DEEPSEEK_API_KEY=... python3 eval/spike.py`
  (reels.txt → grades sheet). Transcription: `python3 eval/transcribe.py` (audio
  already downloaded in eval/audio/ — transcripts can be re-carded without
  re-downloading).
- gstack learnings-log tool is broken ("invalid JSON" for everything incl.
  --help) — append to ~/.gstack/projects/SavedPostIdea/learnings.jsonl directly
  (jq -nc) as a workaround.
- Codex CLI broken (missing vendored binary) — outside voice uses Claude
  subagent fallback.
- Not a git repo yet — git init happens when the build starts.
- Spike grading sheets: eval/grades-*.md (run 1-3), eval/transcribes-*.md
  (phase 2), eval/transcribes-pullback-*.md (v3 pull-back cards).
- Fixtures (eval/fixtures/*.json) are the permanent eval suite seeds; gold cards
  to be added by hand (D5: written blind from captions).
- Whisper built at /tmp/whisper.cpp/build/bin/whisper-cli (model
  eval/models/ggml-base.bin). Brew is blocked by an untrusted mongodb tap —
  don't rely on brew; cmake came via pip.
