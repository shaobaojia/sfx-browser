#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探测三个原始压缩包的清单规模与顶层结构"""
import zipfile, os
Z = "/volume1/主目录/Collection/素材&模板&音库/音效/99_待整理/_原始压缩包"

for fn in sorted(os.listdir(Z)):
    if not fn.lower().endswith(".zip"):
        print("非zip: %s" % fn); continue
    p = os.path.join(Z, fn)
    try:
        z = zipfile.ZipFile(p)
    except Exception as e:
        print("%s\n  !! 无法打开: %s" % (fn, e)); continue
    infos = z.infolist()
    files = [i for i in infos if not i.is_dir()]
    junk = [i for i in files if ("__MACOSX" in i.filename
            or i.filename.split("/")[-1] in (".DS_Store", "Thumbs.db")
            or i.filename.split("/")[-1].startswith("._"))]
    junk_set = set(id(i) for i in junk)
    real = [i for i in files if id(i) not in junk_set]
    tot = sum(i.file_size for i in real)
    print("%s" % fn)
    print("  条目: %d 文件 (+%d junk条目) | 解压后: %.2f GB" % (len(real), len(junk), tot / 1e9))
    tops = {}
    for i in real:
        t = i.filename.split("/")[0] if "/" in i.filename else "(无目录)"
        tops[t] = tops.get(t, 0) + 1
    top_sorted = sorted(tops.items(), key=lambda x: -x[1])
    print("  顶层目录(文件数):")
    for t, c in top_sorted[:15]:
        print("    [%d] %s" % (c, t))
    if len(top_sorted) > 15:
        print("    ... 共 %d 个顶层条目" % len(top_sorted))
    print()
print("DONE")
