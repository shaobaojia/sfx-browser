#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 _垃圾件/ 按 junk_moved_20260919.csv 挪回库里（只动清单内、不覆盖）"""
import csv, os
from collections import Counter

LIB  = "/volume1/主目录/Collection/素材&模板&音库/音效"
JUNK = os.path.join(LIB, "99_待整理/_垃圾件")
CSV  = "/volume1/主目录/Hermes/read/Projects/sfx-browser/organize/junk_moved_20260919.csv"

rows = list(csv.reader(open(CSV, encoding="utf-8-sig")))[1:]
done = skip = 0
for rel, jrel, cat, sz in rows:
    src = os.path.join(JUNK, jrel)
    dst = os.path.join(LIB, rel)
    if not os.path.exists(src):
        print("源缺失，跳过:", jrel); skip += 1; continue
    if os.path.exists(dst):
        print("原位已存在，跳过:", rel); skip += 1; continue
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    os.rename(src, dst)
    done += 1
print("归还 %d 件 | 跳过 %d 件" % (done, skip))
