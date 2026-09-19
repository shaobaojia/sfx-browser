#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清洗最后一个 PUA 残渣：爆炸 烟火\uf028 → 爆炸 烟火"""
import os

D = "/volume1/主目录/Collection/素材&模板&音库/音效/02_中文音效合集/BD音效库/附赠音效库（转场+撞击+音效+环境音）/音效"

hits = [n for n in os.listdir(D) if "\uf028" in n]
for n in hits:
    p = os.path.join(D, n)
    new = n.replace("\uf028", "").strip()
    dst = os.path.join(D, new)
    if os.path.exists(dst):
        print("目标已存在，跳过:", repr(n)); continue
    kind = "目录" if os.path.isdir(p) else "文件"
    os.rename(p, dst)
    print("  %r (%s)  ->  %r" % (n, kind, new))
print("清洗 %d 个" % len(hits))
print("DONE")
