#!/usr/bin/env python3
"""One runnable check for the D1 low-info classifier rules. Run: python3 eval/test_classifier.py"""
from spike import low_info, strip_meta

# Metadata prefix must be stripped before classification
assert strip_meta('4,210 likes, 28 comments - luke.andrew.howland on July 26, 2026: "What all men long for"') == "What all men long for"
assert strip_meta('47K likes, 8,313 comments - idrisaicreative on July 26, 2026: "Kali ini menghadirkan aksi"') == "Kali ini menghadirkan aksi"
assert strip_meta("no metadata here, just a real caption") == "no metadata here, just a real caption"

# Filler captions -> bare save
assert low_info("link in bio") is True
assert low_info("follow @myaccount for part 2") is True
assert low_info("") is True
assert low_info("#ad #sponsored #tools #marketing #growth") is True
assert low_info("DM me for the full list") is True
assert low_info("Comment SHOP for the list") is True          # pure CTA, nothing left after strip
assert low_info("What all men long for") is True              # real hook but 19 chars, nothing actionable

# Real captions must NOT be demoted — even when they contain CTA phrases
assert low_info("3 free AI tools for thumbnails that I actually use every week, tested over six months") is False
assert low_info("Comment “Collections” and I’ll send the link to the best database of short-form video references with over 100 collections across format types, visual hooks and editing styles") is False
assert low_info("here is a real caption with actual substance about productivity systems and how to build them step by step over a weekend") is False
assert low_info("#tools this is a real caption that starts with hashtags but has real content after them") is False

print("classifier: all checks passed")
