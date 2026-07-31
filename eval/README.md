# Ingest spike harness (G2)

The pre-build gate. Answers: can we fetch reel captions from a server, and are
caption-only AI cards good enough — per content type?

## How to run

1. Put 20 reel links in `reels.txt`, weighted toward talking-head educational
   reels (the founder's actual target content).
2. `export DEEPSEEK_API_KEY=sk-...` (OpenAI-compatible endpoint; model/URL
   overridable via `DEEPSEEK_MODEL` / `DEEPSEEK_BASE_URL`, defaults
   `deepseek-v4-flash` / `https://api.deepseek.com`)
3. `python3 eval/spike.py`

## What you get

- `eval/grades-<date>.md` — grading sheet: caption + AI card per reel, with
  blank **Grade** (3=useful, 2=ok, 1=garbage, -=bare save) and **Notes**
  columns. THIS is the decision input.
- `eval/fixtures/*.json` — per-reel records (url, final_url, caption, og
  fields, card). These are the permanent eval suite seeds; add `gold_card`
  by hand (blind, from caption only) per the D5 decision.

## What the results mean

- Status `OK` + good grades on talking heads → caption-only ships.
- Status `OK` but grades mostly 1 on talking heads → **transcription becomes
  MVP-critical** (audio download + speech-to-text; 150s Edge Function cap
  workaround needed). The grading sheet is the evidence.
- Status `SHELL`/`NO_CAPTION`/`HTTP_*` on most → server-side fetch is the
  blocker; T13 gate fails. This is the load-bearing risk the plan exists to
  test.

## Carousels

User decision (2026-07-31): carousels are NOT bare saves. `og:description` is
the caption (often content-rich on slide-decks); `og:image` is the first
slide — the carousel's hook, already captured in every fixture. Grade carousel
cards per content type: if captions alone make good cards, no OCR needed. If
the hook lives only in the on-image text, OCR of the first slide becomes a
spike-gated addition (same pattern as transcription).

Notes: local fetch is from your home IP, not a Supabase datacenter IP — the
datacenter-IP test (T13) runs later via the ingest Edge Function. The
per-hop SSRF validation is production (T19); this harness only logs the
final URL for the dedupe-canonicalization data.
