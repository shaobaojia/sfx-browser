#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""脏名字符清洗：PUA残渣 -> ／（9 个对象，底向上改名，留对照表）"""
import os, csv, sys
from collections import Counter

LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
ORG = "/volume1/主目录/Hermes/read/Projects/sfx-browser/organize"
LOG = os.path.join(ORG, "dirty_renamed_20260919.csv")

def trans(name):
    s = name.replace("\uf022", "／").replace("\uf026", "／")
    s = s.replace("／ ", "／").strip("／").strip()
    return s

targets = []   # (path, depth)
for root, dirs, fns in os.walk(LIB):
    for nm in list(dirs) + fns:
        if any(0xE000 <= ord(c) <= 0xF8FF for c in nm):
            p = os.path.join(root, nm)
            targets.append((p, p.count(os.sep)))

targets.sort(key=lambda t: -t[1])   # 深的先改
print("待清洗: %d 个对象（文件+目录）" % len(targets))
rows = []
for p, _ in targets:
    if not os.path.exists(p):   # 父目录改名后子路径已变——重算
        continue
    d, nm = os.path.split(p)
    new = trans(nm)
    if not new or new == nm:
        print("  跳过(无变化): %r" % nm); continue
    dst = os.path.join(d, new)
    if os.path.exists(dst):
        base, ext = os.path.splitext(dst); k = 2
        while os.path.exists("%s_%d%s" % (base, k, ext)): k += 1
        dst = "%s_%d%s" % (base, k, ext)
    os.rename(p, dst)
    rows.append([os.path.relpath(p, LIB), os.path.relpath(dst, LIB)])
    print("  %r  ->  %r" % (nm, os.path.basename(dst)))

with open(LOG, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["原名(库内相对)", "新名(库内相对)"])
    w.writerows(rows)
print("改名 %d 个；对照表: %s" % (len(rows), LOG))
print("DONE")
