#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回滚：把隔离区文件按 moved.csv 搬回原位置。--dry 只演练。"""
import os, sys, csv
LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
QUAR = "/volume1/主目录/Collection/素材&模板&音库/音效_去重待删_20260919"
CSV = "/volume1/主目录/Hermes/read/Projects/sfx-browser/dedup/moved.csv"
dry = "--dry" in sys.argv
restored = skipped = conflicts = 0
for row in csv.DictReader(open(CSV, encoding="utf-8-sig")):
    rel = row["rel"]
    src = os.path.join(QUAR, rel); dst = os.path.join(LIB, rel)
    if not os.path.exists(src): skipped += 1; continue
    if os.path.exists(dst): conflicts += 1; continue
    if not dry:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        os.rename(src, dst)
    restored += 1
print("restored=%d skipped(missing)=%d conflicts=%d dry=%s" % (restored, skipped, conflicts, dry))
