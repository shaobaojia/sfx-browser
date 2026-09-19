#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""整理回滚 v2：按 organize_moved.csv 把文件搬回原位置。--dry 演练。
跳过 conflict-lost（被覆盖，无文件可回）。"""
import os, sys, csv
LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
CSV = "/volume1/主目录/Hermes/read/Projects/sfx-browser/organize/organize_moved.csv"
dry = "--dry" in sys.argv
ok = skipped = conflicts = lostskip = 0
for row in csv.DictReader(open(CSV, encoding="utf-8-sig")):
    rel, nr, st = row["rel"], row["new_rel"], row.get("status", "")
    if st == "conflict-lost" or not nr:
        lostskip += 1; continue
    src = os.path.join(LIB, nr); dst = os.path.join(LIB, rel)
    if not os.path.exists(src): skipped += 1; continue
    if os.path.exists(dst): conflicts += 1; continue
    if not dry:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        os.rename(src, dst)
    ok += 1
print("restored=%d skipped(missing)=%d conflicts=%d lost-skip=%d dry=%s" % (ok, skipped, conflicts, lostskip, dry))
