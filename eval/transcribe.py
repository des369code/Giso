#!/usr/bin/env python3
"""Spike phase 2: audio transcription for TALKING_HEAD reels.

For each TALKING_HEAD reel in reels.txt: download audio (yt-dlp), transcribe
(whisper-cli), write a card from the transcript (ask_card from spike.py).
Output: transcribes-<ts>.md grading sheet.

Run:  python3 eval/transcribe.py   (needs DEEPSEEK_API_KEY)
Requires: ffmpeg, yt-dlp, whisper-cli, eval/models/ggml-base.bin
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from spike import ask_card

BASE = Path(__file__).resolve().parent
WHISPER_MODEL = BASE / "models" / "ggml-base.bin"
WHISPER_CLI = Path(os.environ.get("WHISPER_CLI", "/tmp/whisper.cpp/build/bin/whisper-cli"))
AUDIO_DIR = BASE / "audio"


def transcribe(url: str, idx: int) -> str:
    AUDIO_DIR.mkdir(exist_ok=True)
    out = AUDIO_DIR / f"{idx:02d}"
    subprocess.run(
        ["yt-dlp", "-x", "--audio-format", "mp3", "--no-playlist", "-o", f"{out}.%(ext)s", url],
        capture_output=True, timeout=180,
        check=True,
    )
    mp3 = next(AUDIO_DIR.glob(f"{idx:02d}.*"))
    subprocess.run(
        [str(WHISPER_CLI), "-m", str(WHISPER_MODEL), "-f", str(mp3), "-otxt", "-of", str(out)],
        capture_output=True, timeout=300,
        check=True,
    )
    return (AUDIO_DIR / f"{idx:02d}.txt").read_text().strip()


def main() -> int:
    if not os.environ.get("DEEPSEEK_API_KEY"):
        print("DEEPSEEK_API_KEY not set")
        return 1
    if not WHISPER_MODEL.exists():
        print(f"model missing: {WHISPER_MODEL}")
        return 1
    if not WHISPER_CLI.exists():
        print(f"whisper-cli missing: {WHISPER_CLI} (set WHISPER_CLI)")
        return 1

    lines = [l for l in (BASE / "reels.txt").read_text().splitlines() if l.strip() and not l.startswith("#")]
    targets = [l for l in lines if l.split()[0].upper() == "TALKING_HEAD"]
    if not targets:
        print("no TALKING_HEAD reels in reels.txt")
        return 0

    rows = []
    for i, line in enumerate(targets, 1):
        url = line.split()[-1]
        print(f"[{i:02d}] {url[:55]}...")
        try:
            txt = transcribe(url, i)
            card = ask_card("Transcript of a reel the user saved:\n" + txt)
            rows.append((i, txt, card))
            print(f"    transcript: {len(txt)} chars | card: {card.get('title', 'ERR')[:40]}")
        except Exception as e:
            rows.append((i, "", {"error": f"{type(e).__name__}: {e}"}))
            print(f"    FAIL: {type(e).__name__}: {e}")

    sheet = BASE / f"transcribes-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}.md"
    lines_out = [
        "# Giso spike phase 2 — audio transcription",
        "",
        "Grade each card: 3 = genuinely useful / 2 = ok / 1 = garbage.",
        "",
        "| # | Transcript (first 220 chars) | Card (title -> what_to_do) | Grade | Notes |",
        "|---|------------------------------|----------------------------|-------|-------|",
    ]
    for i, txt, card in rows:
        if "error" in card:
            ct = f"ERROR: {card['error']}"
        else:
            ct = f"{card.get('title', '')} -> {card.get('what_to_do', '')}"
        lines_out.append(f"| {i} | {txt[:220].replace('|', '/')} | {ct[:220].replace('|', '/')} |  |  |")
    sheet.write_text("\n".join(lines_out) + "\n")
    print(f"\nsheet: {sheet.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
