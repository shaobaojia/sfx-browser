#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小结石清理：垃圾小件+空文件 → 99_待整理/_垃圾件/（保结构、带清单、可还）"""
import os, csv, sys

LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
JUNK = os.path.join(LIB, "99_待整理/_垃圾件")
ORG = "/volume1/主目录/Hermes/read/Projects/sfx-browser/organize"
CSV = os.path.join(ORG, "junk_moved_20260919.csv")

def classify(fn, size):
    low = fn.lower()
    if low == ".ds_store": return "DS_Store"
    e = os.path.splitext(fn)[1].lower()
    if e == ".sfk": return "sfk缓存"
    if e in (".url", ".lnk"): return "广告快捷方式"
    if e == ".db": return "Thumbs.db"
    if fn in ("人人素材网说明文件.rar", "人人素材网.rar"): return "广告包"
    if low == "about.zip": return "about包"
    if size == 0: return "空文件"
    return None

rows = []
skipped_inside = 0
for bucket in ("01_商业音效包", "02_中文音效合集", "03_项目素材", "99_待整理"):
    for root, dirs, fns in os.walk(os.path.join(LIB, bucket)):
        if "_垃圾件" in root: 
            skipped_inside += 1; continue
        for fn in fns:
            p = os.path.join(root, fn)
            try: sz = os.path.getsize(p)
            except OSError: continue
            cat = classify(fn, sz)
            if not cat: continue
            rows.append((p, cat, sz))

print("待挪: %d 件" % len(rows))
from collections import Counter
print("分类:", dict(Counter(r[1] for r in rows)))

moved = 0
out = []
for p, cat, sz in rows:
    rel = os.path.relpath(p, LIB)
    dst = os.path.join(JUNK, rel)
    if os.path.exists(dst):
        base, ext = os.path.splitext(dst); k = 2
        while os.path.exists("%s_%d%s" % (base, k, ext)): k += 1
        dst = "%s_%d%s" % (base, k, ext)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    os.rename(p, dst)
    moved += 1
    out.append([rel, os.path.relpath(dst, JUNK), cat, sz])

with open(CSV, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["原相对路径(库根)", "垃圾件内相对路径", "类别", "大小"])
    w.writerows(out)

with open(os.path.join(JUNK, "说明.txt"), "w", encoding="utf-8") as f:
    f.write("本文件夹 = 2026-09-19 结构体检后移出的垃圾小件（只移不删）。\n")
    f.write("内容：macOS 元数据(.DS_Store)、SoundForge 峰值缓存(.sfk)、广告快捷方式(.url/.lnk)、\n")
    f.write("Thumbs.db、广告小包、0 字节坏件。全清单：organize/junk_moved_20260919.csv\n")
    f.write("还原：按 CSV 反着挪回即可（脚本 junk_restore.py 在 sfx-browser 仓库 organize/ 下）。\n")
    f.write("确认无用后可整体删除。\n")

print("已挪 %d 件 -> 99_待整理/_垃圾件/" % moved)
print("清单: %s" % CSV)
print("DONE")
