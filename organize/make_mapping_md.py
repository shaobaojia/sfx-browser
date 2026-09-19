#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 整理映射表.md（条目级）：从 organize_moved.csv 聚合「源顶层 → 目标」"""
import os, csv
from collections import Counter, OrderedDict
ORG = "/volume1/主目录/Hermes/read/Projects/sfx-browser/organize"
MOVED = os.path.join(ORG, "organize_moved.csv")
OUT = os.path.join(ORG, "整理映射表.md")

rows = list(csv.reader(open(MOVED, encoding="utf-8-sig")))[1:]
agg = Counter(); st_agg = {}
for rel, nr, st in rows:
    if st == "conflict-lost":
        continue
    parts = rel.split("/")
    if parts[0] == "音效":
        if len(parts) == 1:
            top = "音效"
        elif parts[1] == "音效":
            top = "音效/音效/BD音效库"
        else:
            top = "音效/" + parts[1]
    else:
        top = parts[0]
    nparts = nr.split("/")
    grp = "/".join(nparts[:2]) if len(nparts) >= 2 else nr
    key = (grp, top)
    agg[key] += 1

by_grp = OrderedDict()
for (grp, top), n in sorted(agg.items()):
    by_grp.setdefault(grp, []).append((top, n))

lines = []
lines.append("# 音效库·整理映射表（条目级）")
lines.append("")
lines.append("> 生成: 2026-09-19 | 数据源: organize_moved.csv | 每行 = 一个源顶层 → 目标父级（含文件数）")
lines.append("")
total = sum(agg.values())
lines.append("总计 **%d** 个文件归位（另有 12 个 conflict-lost，详见 organize_lost_files.json）" % total)
lines.append("")
for grp, items in by_grp.items():
    lines.append("## → %s（%d 项 / %d 文件）" % (grp, len(items), sum(n for _, n in items)))
    lines.append("")
    lines.append("| 源 | 文件数 |")
    lines.append("|---|---|")
    shown = sorted(items, key=lambda x: -x[1])
    for top, n in shown:
        lines.append("| %s | %d |" % (top.replace("|", "\\|"), n))
    lines.append("")

open(OUT, "w", encoding="utf-8").write("\n".join(lines))
print("wrote", OUT, "groups:", len(by_grp), "rows:", len(agg), "total files:", total)
