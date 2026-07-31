#!/usr/bin/env python3
"""Giso ingest spike harness (eval/ stage 1).

Takes reel links from reels.txt, fetches each page, extracts the caption
(og:description), runs the low-info classifier, asks Claude Haiku to write an
action card, and produces a grading sheet plus per-reel fixtures.

The grading sheet is what the founder fills in (Grade / Notes columns) — that
grade, per content type, is the pre-build gate decision. Fixtures become the
permanent eval suite seeds (gold cards added by hand later).

Run:  python3 eval/spike.py         (needs ANTHROPIC_API_KEY in env)
Reels: eval/reels.txt — one per line:  TYPE URL   (TYPE optional, e.g. TALKING_HEAD)
"""

import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent

CAPTION_RE = re.compile(
    r"<meta[^>]+(?:property|name)=[\"'](?:og:)?description[\"'][^>]+content=[\"'](.*?)[\"']",
    re.I | re.S,
)
TITLE_RE = re.compile(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']', re.I | re.S)
IMAGE_RE = re.compile(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](.*?)["\']', re.I | re.S)

# Instagram og:description carries a metadata prefix that is NOT the caption:
#   "4,210 likes, 28 comments - luke.andrew.howland on July 26, 2026: "caption""
# Strip it before the classifier and the card call.
META_PREFIX_RE = re.compile(
    r"^[\d.,]+[KkMm]?\s*(?:likes?|views?),\s*[\d.,]+[KkMm]?\s*comments?\s*-\s*[\w.\-]+\s+on\s+[A-Za-z]+\s+\d{1,2},\s*\d{4}:\s*\"?",
    re.I,
)


def strip_meta(caption: str) -> str:
    return META_PREFIX_RE.sub("", caption, count=1).rstrip('"')


# D1 decision: rule-based low-info classifier (pattern list + length floor).
# V2 (spike 2026-07-31): a CTA phrase inside real content is NOT filler — strip
# CTA phrases + hashtags, then measure what remains. Only CTA-only captions
# ("Comment SHOP", "link in bio") collapse to nothing and become bare saves.
LOW_INFO_PATTERNS = [
    "link in bio", "linkinbio", "follow me", "follow @", "comment",
    "dm me", "part 2", "like and share", "like and follow", "save this post",
    "swipe", "credit:", "repost", "share this", "tag someone", "drop a comment",
]
MIN_CAPTION_LEN = 30
MIN_CONTENT_LEN = 30  # meaningful text left after stripping CTAs + hashtags

CARD_SYSTEM = (
    "You turn Instagram post captions into action cards for a personal knowledge app. "
    "Return JSON only with fields: title, what_it_says, what_to_do.\n"
    "Rules:\n"
    "- Write like a sharp friend, not an AI. Concrete, specific, zero filler.\n"
    "- title: under 8 words, names the actual subject.\n"
    "- what_it_says: name the actual thing — the tool, site, resource, or idea — explicitly. "
    "Never write 'this resource' or 'this post'.\n"
    "- what_to_do: ONE clear, specific action, under 20 words, phrased as a direct instruction "
    "the reader could do today (e.g. 'Open the directory and pick an API for your next project').\n"
    "- BANNED in what_to_do: 'bookmark this', 'save this', 'remember this', 'note this', "
    "'consider', 'keep in mind' — they are lazy and vague.\n"
    "- IGNORE engagement bait: 'comment X', 'follow for more', 'DM for the link', 'link in bio' "
    "are Instagram tactics, NOT actions for the user. Never make them the what_to_do.\n"
    "- PULL-BACK (founder rule, 2026-07-31): the card is a memory trigger, not the full article. "
    "Where the video contains depth the card cannot hold — an exact script, prompt, list, quote, "
    "or story — end what_to_do with ONE short clause naming it: 'Open the reel to see the exact "
    "prompt he reads.' Only when the card fully covers the content (resource links, tool lists) "
    "is a pull-back unnecessary.\n"
    "- If the caption has genuinely no content, return "
    '{"title": "Bare save", "what_it_says": "", "what_to_do": ""}.\n'
    "- Output JSON only, no markdown fences."
)


def clean(s: str) -> str:
    return html.unescape(s).replace("\n", " ").strip()


def low_info(caption: str) -> bool:
    """True when the caption is filler and would make a garbage card."""
    c = caption.lower()
    if len(c) < MIN_CAPTION_LEN:
        return True
    stripped = re.sub(r"#\w+\s*", "", c)
    for p in LOW_INFO_PATTERNS:
        stripped = stripped.replace(p, "")
    stripped = re.sub(r"[\s.,!?;:'\"“”()@]+", " ", stripped).strip()
    return len(stripped) < MIN_CONTENT_LEN


def fetch(url: str, timeout: int = 15):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.geturl(), r.read().decode("utf-8", "replace")


def meta(page: str, pattern: re.Pattern) -> str:
    m = pattern.search(page)
    return clean(m.group(1)) if m else ""


def ask_card(caption: str) -> dict:
    """Card via DeepSeek (OpenAI-compatible chat completions).

    T4 hardening: retry once on malformed JSON — the gateway intermittently
    returns prose/fences instead of JSON despite response_format.
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    base = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
    for attempt in (1, 2):
        user_msg = caption
        fmt = {"type": "json_object"}
        if attempt == 2:
            # Reasoning backends eat the token budget and never reach the JSON
            # answer; drop json mode and demand it in plain words instead.
            fmt = None
            user_msg = caption + "\n\nReturn ONLY valid JSON with fields title, what_it_says, what_to_do. No other text."
        payload = {
            "model": model,
            "max_tokens": 4000,
            "messages": [
                {"role": "system", "content": CARD_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
        }
        if fmt:
            payload["response_format"] = fmt
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            base.rstrip("/") + "/chat/completions",
            data=body,
            headers={"Authorization": f"Bearer {api_key}", "content-type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=90) as r:
            data = json.loads(r.read().decode())
        # Some gateway backends are reasoning-mode: content is empty and the
        # answer lands in reasoning_content instead.
        msg = data["choices"][0]["message"]
        text = (msg.get("content") or msg.get("reasoning_content") or "").strip()
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", text, re.S)  # last-ditch: largest JSON block
            if m:
                try:
                    return json.loads(m.group(0))
                except json.JSONDecodeError:
                    pass
            if attempt == 2:
                raise ValueError(f"bad JSON after retry: {text[:200]!r}")


def trunc(s: str, n: int = 90) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def slug_from(url: str) -> str:
    m = re.search(r"/(?:reel|p)/([A-Za-z0-9_-]+)", url)
    return m.group(1) if m else re.sub(r"[^A-Za-z0-9_-]+", "-", url)[:40]


def main() -> int:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        print("DEEPSEEK_API_KEY not set — cards will be skipped; extraction+classifier still run.")
    reels_file = BASE / "reels.txt"
    if not reels_file.exists():
        print(f"missing {reels_file} — add one reel per line:  TYPE URL")
        return 1
    reels = []
    for line in reels_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[1].startswith("http"):
            reels.append((parts[0].upper(), parts[1]))
        else:
            reels.append(("UNKNOWN", parts[0]))
    if not reels:
        print("no reels in reels.txt — add lines like:  TALKING_HEAD https://www.instagram.com/reel/...")
        return 0

    (BASE / "fixtures").mkdir(exist_ok=True)
    results = []
    for i, (rtype, url) in enumerate(reels, 1):
        rec = {"n": i, "type": rtype, "url": url}
        try:
            final_url, page = fetch(url)
            rec["final_url"] = final_url
            rec["caption_raw"] = meta(page, CAPTION_RE)
            rec["caption"] = strip_meta(rec["caption_raw"])
            rec["og_title"] = meta(page, TITLE_RE)
            rec["og_image"] = meta(page, IMAGE_RE)
            if not rec["caption_raw"]:
                # T13 sharpen: HTTP 200 "error shells" carry zero post data.
                rec["status"] = "SHELL" if "httpErrorPage" in page else "NO_CAPTION"
            else:
                rec["status"] = "LOW_INFO" if low_info(rec["caption"]) else "OK"
        except urllib.error.HTTPError as e:
            rec["status"] = f"HTTP_{e.code}"
        except Exception as e:
            rec["status"] = f"FETCH_FAIL: {type(e).__name__}"

        rec["card"] = None
        if rec.get("status") == "OK" and api_key:
            try:
                rec["card"] = ask_card(rec["caption"])
            except urllib.error.HTTPError as e:
                rec["card"] = {"error": f"API_FAIL HTTP_{e.code}"}
            except Exception as e:
                rec["card"] = {"error": f"PARSE_FAIL: {e}"}
        rec["gold_card"] = ""
        (BASE / "fixtures" / f"{i:02d}-{slug_from(url)}.json").write_text(
            json.dumps(rec, indent=2, ensure_ascii=False)
        )
        results.append(rec)
        print(f"[{i:02d}] {rec['status']:<10} {rtype:<14} {trunc(url, 60)}")

    sheet = BASE / f"grades-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}.md"
    lines = [
        "# Giso ingest spike — grading sheet",
        "",
        "Grade each card: **3** = genuinely useful / **2** = ok / **1** = garbage / **- (bare save)**. "
        "Fill Notes for failures. This decides caption-only vs transcription (gate).",
        "",
        "| # | Type | Status | Caption | AI card (title → what_to_do) | Grade | Notes |",
        "|---|------|--------|---------|------------------------------|-------|-------|",
    ]
    for r in results:
        card = r.get("card") or {}
        if "error" in card:
            card_txt = f"⚠ {card['error']}"
        elif card.get("what_to_do"):
            card_txt = f"{card.get('title','')} → {card['what_to_do']}"
        elif card:
            card_txt = f"{card.get('title','')} → (no what_to_do)"
        else:
            card_txt = "(no card — bare save)"
        lines.append(
            f"| {r['n']} | {r['type']} | {r['status']} | {trunc(r.get('caption',''),90)} | "
            f"{trunc(card_txt, 120)} |  |  |"
        )
    sheet.write_text("\n".join(lines) + "\n")
    print(f"\ngrading sheet: {sheet.name}   fixtures: eval/fixtures/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
