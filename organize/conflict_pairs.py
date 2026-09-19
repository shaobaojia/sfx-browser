#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""命名冲突分析：200 件冲突文件 vs 各自目标位置现存版本，逐一 md5 对比"""
import os, hashlib, csv
from collections import Counter
LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
CF = os.path.join(LIB, "99_待整理/_命名冲突")
ORG = "/volume1/主目录/Hermes/read/Projects/sfx-browser/organize"

def md5f(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b: break
            h.update(b)
    return h.hexdigest()

rows = []
for root, dirs, fns in os.walk(CF):
    for fn in fns:
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, CF)
        tgt = os.path.join(LIB, rel)
        s1 = os.path.getsize(p)
        h1 = md5f(p)
        if os.path.exists(tgt):
            s2 = os.path.getsize(tgt)
            h2 = md5f(tgt)
            same = (h1 == h2)
        else:
            s2 = None; h2 = None; same = None
        rows.append({"rel": rel, "s_conf": s1, "s_tgt": s2, "same": same,
                     "h_conf": h1, "h_tgt": h2})

cnt = Counter("same" if r["same"] is True else ("diff" if r["same"] is False else "no-target") for r in rows)
print("冲突文件总数:", len(rows))
print("分类:", dict(cnt))
byb = Counter(r["rel"].split("/")[0] for r in rows)
print("按桶:", dict(byb))

same = [r for r in rows if r["same"] is True]
print("\n== 字节完全相同（纯冗余）: %d 件 ==" % len(same))
for r in same[:60]:
    print("   %s | %d B" % (r["rel"], r["s_conf"]))
if len(same) > 60: print("   …(共 %d)" % len(same))

diffs = [r for r in rows if r["same"] is False]
print("\n== 内容不同（真·多版本）: %d 件，样例 ==" % len(diffs))
for r in sorted(diffs, key=lambda x: -abs((x["s_tgt"] or 0) - x["s_conf"]))[:18]:
    print("   冲突区 %s B  vs  目标区 %s B | %s" % (r["s_conf"], r["s_tgt"], r["rel"]))

with open(os.path.join(ORG, "conflict_pairs.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["rel", "大小_冲突区", "大小_目标区", "字节相同?", "md5_冲突区", "md5_目标区"])
    for r in rows:
        w.writerow([r["rel"], r["s_conf"], r["s_tgt"], r["same"], r["h_conf"], r["h_tgt"]])
print("\n已写 conflict_pairs.csv")
