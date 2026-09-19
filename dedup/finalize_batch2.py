#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""汇总两批搬迁数、更新隔离区说明 + 执行报告附录。"""
import os, json, csv
LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
QUAR = "/volume1/主目录/Collection/素材&模板&音库/音效_去重待删_20260919"
DED = "/volume1/主目录/Hermes/read/Projects/sfx-browser/dedup"

def score(rel):
    sc = rel.count("/") * 100 + len(rel)
    for bad in ("备用", "质量一般", "（1）", "(1)", "副本", "copy"):
        if bad in rel: sc += 2000
    segs = rel.split("/")
    for i in range(len(segs) - 1):
        if segs[i] and segs[i] == segs[i + 1]: sc += 800
    return sc

rows = list(csv.DictReader(open(os.path.join(DED, "moved.csv"), encoding="utf-8-sig")))
tot_files = len(rows); tot_bytes = sum(int(r["size_bytes"]) for r in rows)
d = json.load(open(os.path.join(DED, "recheck_20260919.json"), encoding="utf-8"))
b2 = set()
for g in d["nonaudio_true_clusters"]:
    mem = sorted((str(m[0]), int(m[1])) for m in g)
    keep = min(mem, key=lambda x: score(x[0]))
    for rel, sz in mem:
        if rel != keep[0]: b2.add(rel)
b2_files = sum(1 for r in rows if r["rel"] in b2)
b2_bytes = sum(int(r["size_bytes"]) for r in rows if r["rel"] in b2)
b1_files = tot_files - b2_files; b1_bytes = tot_bytes - b2_bytes
gib = tot_bytes / 2**30

readme = """【这是什么】
音效库去重的隔离区（2026-09-19 创建）。
  第一批：%d 个音频重复件（首轮去重）
  第二批：%d 个非音频重复件（封面/说明/音色文件等，复检时补查）
  合计：%d 个文件 / %.1f GiB
全部经「全量 md5 逐字节」确认与库中留存副本完全相同；目录结构与原位置一致。

【怎么核对】
随便挑几组，和库里保留的那份对比——内容应 100%% 一致（字节级相同）。

【反悔怎么办】一键回滚到原位置（可先加 --dry 演练）：
python3 /volume1/主目录/Hermes/read/Projects/sfx-browser/dedup/restore_from_quarantine.py

【确认没问题后】删除本文件夹即可释放 %.1f GiB：
rm -rf "/volume1/主目录/Collection/素材&模板&音库/音效_去重待删_20260919"

【详细记录】/volume1/主目录/Hermes/read/Projects/sfx-browser/dedup/
""" % (b1_files, b2_files, tot_files, gib, gib)
open(os.path.join(QUAR, "说明.txt"), "w", encoding="utf-8").write(readme)

add = """

## 补充：复检阶段（2026-09-19）
- 音频全库复检（recheck.py）：95,122 个尺寸撞车 → 指纹 → 全量 md5，**0 漏网真重复**（recheck_20260919.json）
- 非音频文件（封面/说明/音色二进制等）首轮未覆盖，本次补查：**%d 件冗余 → 已并入本隔离区**
- 隔离区合计：%d 件 / %.1f GiB（moved.csv 已含全部批次，回滚不影响）
- 0 字节文件 9 个保留（不占空间）
""" % (b2_files, tot_files, gib)
with open(os.path.join(DED, "去重执行报告_2026-09-19.md"), "a", encoding="utf-8") as f:
    f.write(add)

print("TOTALS: total=%d (b1=%d b2=%d) %.2f GiB | b2 %.1f MB" %
      (tot_files, b1_files, b2_files, gib, b2_bytes / 2**20))
