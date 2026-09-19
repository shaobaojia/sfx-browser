#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""去重执行后的独立复核：结构审计 + 现场重哈希抽样。"""
import json, os, hashlib, random, csv, time
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

def md5f(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b: break
            h.update(b)
    return h.hexdigest()

t0 = time.time()
cl = json.load(open(os.path.join(DED, "fullhash.json"), encoding="utf-8"))["clusters"]
print("clusters:", len(cl))

# A) 结构审计：每簇 = 库中恰好1份 + 隔离区恰好count-1份 + 无两边共存
problems = []; computed_moved = set(); pair = {}
for c in cl:
    keep = min(c["members"], key=score)
    lib_cnt = quar_cnt = both = 0
    for m in c["members"]:
        lp = os.path.exists(os.path.join(LIB, m)); qp = os.path.exists(os.path.join(QUAR, m))
        if lp and qp: both += 1
        if lp: lib_cnt += 1
        if qp: quar_cnt += 1
        if m != keep: computed_moved.add(m); pair[m] = keep
    if lib_cnt != 1 or quar_cnt != c["count"] - 1 or both:
        problems.append({"head": c["members"][0][:70], "lib": lib_cnt, "quar": quar_cnt, "count": c["count"], "both": both})
print("A) 结构审计: 异常 %d 簇 %s" % (len(problems), problems[:8]))
print("   占用统计: 库中保留 %d 份 | 隔离区 %d 份" % (len(cl), len(computed_moved)))

# B) moved.csv 与簇计算的一致性
csv_moved = set()
for row in csv.DictReader(open(os.path.join(DED, "moved.csv"), encoding="utf-8-sig")):
    csv_moved.add(row["rel"])
print("B) moved.csv: %d 条 | 差集 csv-only=%d / computed-only=%d" %
      (len(csv_moved), len(csv_moved - computed_moved), len(computed_moved - csv_moved)))

# C) 189 个孤本（无真重复）确认仍在库
quick = json.load(open(os.path.join(DED, "scan_quick.json"), encoding="utf-8"))
all_m = set()
for c in quick["clusters"]: all_m.update(c["members"])
true_m = set()
for c in cl: true_m.update(c["members"])
singles = sorted(all_m - true_m)
miss = [s for s in singles if not os.path.exists(os.path.join(LIB, s))]
print("C) 孤本复核: %d 个 | 不在库中: %d" % (len(singles), len(miss)))

# D) 现场重哈希：TOP10 大簇 + 4 个误报案例簇 全量 + 500 个随机搬迁件
rec = {}
for row in csv.DictReader(open(os.path.join(DED, "full_md5.csv"), encoding="utf-8-sig")):
    rec[row["rel"]] = row["md5"]
tricky_subs = ["23 Bull Roar", "PREL_SSFX_COMP_SP02.52.C", "PREL_SSFX_ASCEND_PO01.9.C", "SSFX_IE_027.R"]
test_clusters = []; seen = set()
def add_cluster(c):
    if id(c) not in seen:
        seen.add(id(c)); test_clusters.append(c)
for c in cl[:10]: add_cluster(c)
for sub in tricky_subs:
    for c in cl:
        if any(sub in m for m in c["members"]):
            add_cluster(c); break
random.seed(20260919)
rand_moved = random.sample(sorted(pair.keys()), 500)
targets = []
for c in test_clusters:
    keep = min(c["members"], key=score)
    for m in c["members"]:
        if m != keep: targets.append((m, keep))
for m in rand_moved: targets.append((m, pair[m]))
bad1 = []; bad2 = []; nbytes = 0
for m, keep in targets:
    hq = md5f(os.path.join(QUAR, m)); hk = md5f(os.path.join(LIB, keep))
    nbytes += os.path.getsize(os.path.join(QUAR, m)) * 2
    if hq != hk: bad1.append((m, keep))
    if hq != rec.get(m) or hk != rec.get(keep): bad2.append((m, keep))
print("D) 现场重哈希: %d 对文件 / %.2f GiB | 内容不一致: %d" % (len(targets), nbytes / 2**30, len(bad1)))
print("E) 与 md5 记录比对: 不一致: %d" % len(bad2))
for b in bad1[:5]: print("   BAD-CONTENT:", b[0][:70], "|", b[1][:70])
for b in bad2[:5]: print("   BAD-RECORD:", b[0][:70])
ok = (not problems) and not (csv_moved - computed_moved) and not (computed_moved - csv_moved) and not miss and not bad1 and not bad2
print("VERDICT:", "ALL-CLEAN" if ok else "PROBLEMS-FOUND", "| %.1fs" % (time.time() - t0))
