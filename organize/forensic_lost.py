#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""取证：找出被覆盖的12个文件 + 从隔离区找恢复源"""
import os, sys, csv, json, collections
sys.path.insert(0, "/volume1/主目录/Hermes/read/Projects/sfx-browser/organize")
import organize_execute as o
LIB = o.LIB; ORG = o.ORG
DED = "/volume1/主目录/Hermes/read/Projects/sfx-browser/dedup"
QUAR = "/volume1/主目录/Collection/素材&模板&音库/音效_去重待删_20260919"

# 1) 多源冲突组（moved.csv 冲突行按 dst 分组）
rows = list(csv.reader(open(os.path.join(ORG, "organize_moved.csv"), encoding="utf-8-sig")))[1:]
groups = collections.OrderedDict()
for rel, nr, st in rows:
    if st == "conflict":
        groups.setdefault(nr, []).append(rel)
dups = {k: v for k, v in groups.items() if len(v) > 1}
print("冲突 dst 总数:", len(groups), " 多源组:", len(dups))
lost = []
for nr, rels in dups.items():
    print("\n[DUP k=%d] %s" % (len(rels), nr))
    for i, r in enumerate(rels):
        tag = "丢失(被覆盖)" if i < len(rels) - 1 else "存活"
        print("   %s: %s" % (tag, r))
        if i < len(rels) - 1:
            lost.append((r, nr))
print("\n需恢复文件数(预期12):", len(lost))

# 2) fullhash 结构探测
fh = json.load(open(os.path.join(DED, "fullhash.json"), encoding="utf-8"))
print("\nfullhash 类型:", type(fh).__name__, " 顶层长度:", len(fh))
clusters = []
if isinstance(fh, dict):
    it = iter(fh.items()); k0, v0 = next(it)
    print("样例 key:", repr(k0)[:60], " value 类型:", type(v0).__name__, " len:", len(v0) if hasattr(v0, '__len__') else '-')
    if isinstance(v0, list) and (not v0 or isinstance(v0[0], str)):
        clusters = list(fh.items())
    elif isinstance(v0, dict):
        print("value dict sample:", json.dumps(v0, ensure_ascii=False)[:200]); sys.exit(1)
    else:
        print("未知 value 结构"); sys.exit(1)
elif isinstance(fh, list):
    print("list 首元素:", json.dumps(fh[0], ensure_ascii=False)[:200])
    sys.exit(1)

path2clus = {}
for h, paths in clusters:
    for p in paths:
        path2clus[p] = (h, paths)
print("簇数:", len(clusters), " 路径数:", len(path2clus))
sam = next(iter(path2clus.items()))
print("路径样例:", repr(sam[0])[:120])

# 3) 去重 moved.csv 结构
drows = list(csv.reader(open(os.path.join(DED, "moved.csv"), encoding="utf-8-sig")))
print("\ndedup moved.csv 表头:", drows[0])
for r in drows[1:3]: print("  样例:", [x[:80] for x in r])
dmap = {}
for r in drows[1:]:
    dmap[r[0]] = r[1]

def resolve_q(path_like):
    if not path_like: return None
    cands = [path_like]
    if not path_like.startswith("/"):
        cands.insert(0, os.path.join(QUAR, path_like))
    # 有时带根名或纯相对
    cands.append(os.path.join(QUAR, path_like.split("音效_去重待删_20260919/", 1)[-1]) if "音效_去重待删" in path_like else None)
    for c in cands:
        if c and os.path.exists(c): return c
    return None

def find_alt(b):
    cl = path2clus.get(b)
    if not cl:
        # 试试带/不带前缀变体
        return None, "不在fullhash样本集"
    h, paths = cl
    for m in paths:
        if m == b: continue
        q = resolve_q(dmap.get(m))
        if q: return q, "隔离区副本(%s)" % os.path.basename(m)
        if os.path.exists(m): return m, "原始路径仍在(%s)" % m
        t = o.T(m)
        if t and os.path.exists(os.path.join(LIB, t)): return os.path.join(LIB, t), "现库路径(%s)" % t
    return None, "簇内无现存副本 | 簇成员=%d" % len(paths)

print("\n== 恢复源搜索 ==")
results = []
for b, nr in lost:
    src, why = find_alt(b)
    results.append({"lost_rel": b, "intended": nr, "recover_src": src, "why": why})
    print("\nLOST:", b)
    print("   目标落点:", nr)
    print("   恢复源:", src)
    print("   说明:", why)

json.dump(results, open(os.path.join(ORG, "recovery_plan.json"), "w"), ensure_ascii=False, indent=1)
print("\n已写 recovery_plan.json")
