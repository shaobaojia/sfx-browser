#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""跨类残件归仓：'.wav' 残件 → 隔离区；更新说明/报告/合计。"""
import os, json, csv, hashlib
LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
QUAR = "/volume1/主目录/Collection/素材&模板&音库/音效_去重待删_20260919"
DED = "/volume1/主目录/Hermes/read/Projects/sfx-browser/dedup"

def md5f(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b: break
            h.update(b)
    return h.hexdigest()

def score(rel):
    sc = rel.count("/") * 100 + len(rel)
    for bad in ("备用", "质量一般", "（1）", "(1)", "副本", "copy"):
        if bad in rel: sc += 2000
    segs = rel.split("/")
    for i in range(len(segs) - 1):
        if segs[i] and segs[i] == segs[i + 1]: sc += 800
    return sc

rel = "音效/Pro Sound Effect/24.Historical Military/.wav"
twin = "24.Historical Military/03 Cannons ; Large Single Fire W Fuse.wav"
src = os.path.join(LIB, rel); dst = os.path.join(QUAR, rel)
hs = md5f(src); ht = md5f(os.path.join(LIB, twin))
print("md5 残件=%s 正本=%s 相同=%s" % (hs[:10], ht[:10], hs == ht))
assert hs == ht, "内容不一致，拒绝移动！"
size = os.path.getsize(src)
if os.path.exists(dst):
    print("注意：目标已存在（可能已搬过）")
else:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    os.rename(src, dst)
    with open(os.path.join(DED, "moved.csv"), "a", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerow([rel, size])
    print("已移入隔离区: %d bytes" % size)

# 重算合计 + 重写说明 + 报告附录
rows = list(csv.DictReader(open(os.path.join(DED, "moved.csv"), encoding="utf-8-sig")))
tot = len(rows); totb = sum(int(r["size_bytes"]) for r in rows)
d = json.load(open(os.path.join(DED, "recheck_20260919.json"), encoding="utf-8"))
b2set = set()
for g in d["nonaudio_true_clusters"]:
    mem = sorted((str(m[0]), int(m[1])) for m in g)
    keep = min(mem, key=lambda x: score(x[0]))
    for r2, sz in mem:
        if r2 != keep[0]: b2set.add(r2)
b2 = sum(1 for r in rows if r["rel"] in b2set)
b3 = 1
b1 = tot - b2 - b3
gib = totb / 2**30
readme = """【这是什么】
音效库去重的隔离区（2026-09-19 创建）。
  第一批：%d 个音频重复件（首轮去重）
  第二批：%d 个非音频重复件（封面/说明/音色文件等，复检补查）
  第三批：1 个跨类残件（音效/Pro Sound Effect/24.Historical Military/.wav，名字残缺躲过索引）
  合计：%d 个文件 / %.2f GiB
全部经「全量 md5 逐字节」确认与库中留存副本完全相同；目录结构与原位置一致。

【怎么核对】
随便挑几组，和库里保留的那份对比——内容应 100%% 一致（字节级相同）。

【反悔怎么办】一键回滚到原位置（可先加 --dry 演练）：
python3 /volume1/主目录/Hermes/read/Projects/sfx-browser/dedup/restore_from_quarantine.py

【确认没问题后】删除本文件夹即可释放 %.2f GiB：
rm -rf "/volume1/主目录/Collection/素材&模板&音库/音效_去重待删_20260919"

【详细记录】/volume1/主目录/Hermes/read/Projects/sfx-browser/dedup/
""" % (b1, b2, tot, gib, gib)
open(os.path.join(QUAR, "说明.txt"), "w", encoding="utf-8").write(readme)
add = """
## 跨类核对补充（2026-09-19）
- 跨类比对（非音频 4,037 个 × 其中尺寸撞音频的 673 个全查）：发现 1 对——`音效/Pro Sound Effect/24.Historical Military/.wav`（文件名残缺、被扩展名解析漏出索引）与 `24.Historical Military/03 Cannons ; Large Single Fire W Fuse.wav` 字节相同 → 残件已移入隔离区。
- 至此三种配对全部核清：**音频↔音频、非音频↔非音频、跨类——库内任意两文件之间已无字节级重复**。
- 0 字节空文件 9 个保留（不占空间）。
"""
with open(os.path.join(DED, "去重执行报告_2026-09-19.md"), "a", encoding="utf-8") as f:
    f.write(add)
print("TOTALS: total=%d (b1=%d b2=%d b3=%d) %.2f GiB" % (tot, b1, b2, b3, gib))
