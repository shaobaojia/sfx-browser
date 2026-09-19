#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""恢复源搜索 v2：适配 fullhash.json 真实结构"""
import os, sys, csv, json
sys.path.insert(0, "/volume1/主目录/Hermes/read/Projects/sfx-browser/organize")
import organize_execute as o
LIB = o.LIB; ORG = o.ORG
DED = "/volume1/主目录/Hermes/read/Projects/sfx-browser/dedup"
QUAR = "/volume1/主目录/Collection/素材&模板&音库/音效_去重待删_20260919"

# 1) 探测 fullhash 结构
fh = json.load(open(os.path.join(DED, "fullhash.json"), encoding="utf-8"))
print("== fullhash 顶层键 ==")
for k, v in fh.items():
    print("  ", repr(k), type(v).__name__, len(v) if hasattr(v, "__len__") else "-")

# 找簇容器
clusters = None
for k, v in fh.items():
    if k == "summary": continue
    if isinstance(v, dict):
        # hash -> [files]?
        some = list(v.items())[:2]
        print("  探测", k, ": dict, 样例键", repr(some[0][0])[:50], "值类型", type(some[0][1]).__name__)
        if isinstance(some[0][1], list) and (not some[0][1] or isinstance(some[0][1][0], str)):
            clusters = list(v.items()); break
        elif isinstance(some[0][1], dict):
            print("    值dict样例:", json.dumps(some[0][1], ensure_ascii=False)[:160])
    elif isinstance(v, list):
        print("  探测", k, ": list, 首元素类型", type(v[0]).__name__)
        print("    首元素:", json.dumps(v[0], ensure_ascii=False)[:200] if not isinstance(v[0], str) else repr(v[0]))
        if isinstance(v[0], list):
            clusters = [("clus_%d" % i, x) for i, x in enumerate(v)]; break
        elif isinstance(v[0], dict):
            # 猜键
            d0 = v[0]; print("    dict键:", list(d0.keys())[:8])
            hk = None
            for cand in ("hash", "md5", "h"):
                if cand in d0: hk = cand; break
            fk = None
            for cand in ("files", "paths", "members", "items"):
                if cand in d0: fk = cand; break
            if hk and fk:
                clusters = [(x[hk], x[fk]) for x in v]; break
if clusters is None:
    print("!! 未能识别簇结构，停止"); sys.exit(1)
print("簇数:", len(clusters), " 样例簇键:", repr(clusters[0][0])[:50], " 成员数:", len(clusters[0][1]))

path2clus = {}
for h, paths in clusters:
    for p in paths:
        path2clus[p] = (h, paths)
print("路径索引:", len(path2clus))
sp = next(iter(path2clus.items()))
print("路径样例:", repr(sp[0])[:130])

# 2) dedup moved.csv
drows = list(csv.reader(open(os.path.join(DED, "moved.csv"), encoding="utf-8-sig")))
print("\n== dedup moved.csv 表头:", drows[0])
for r in drows[1:3]: print("  样例:", [x[:90] for x in r])
dmap = {}
for r in drows[1:]:
    dmap[r[0]] = r[1]

def resolve_q(pl):
    if not pl: return None
    for c in [pl, os.path.join(QUAR, pl) if not pl.startswith("/") else None,
              os.path.join(QUAR, pl.split("音效_去重待删_20260919/", 1)[-1]) if "音效_去重待删" in pl else None]:
        if c and os.path.exists(c): return c
    return None

# 3) 12 个丢失文件（从 recovery_plan 之前的输出固化为清单）
LOST = [
 "Pro Sound Effect/10 Body Sounds/63 Two Single Body Falls On Gravel.wav",
 "Pro Sound Effect/12 Sports & Boats/15 Wooden Bat Drops Onto Dirt Surface #1.wav",
 "Pro Sound Effect/19 Beeps,Bells,Buzzers,Rumbles,Tools/48 Very Low Frequency, Ominous, Underwater Rumble.wav",
 "Pro Sound Effect/19 Beeps,Bells,Buzzers,Rumbles,Tools/49 Avalanche Rumble With Rocks Rolling And Debris.wav",
 "Pro Sound Effect/24.Historical Military/46 Sword ; Single Swish.wav",
 "Pro Sound Effect/32.Household/85 Toilet Paper From Roll,Pulling Off.wav",
 "Pro Sound Effect/38.Foley;Cloth,Nylon,Leather,Velcro,Zippers,Bag/06 Cloth,Grabs With Heavy,Rustle.wav",
 "Pro Sound Effect/38.Foley;Cloth,Nylon,Leather,Velcro,Zippers,Bag/28 Cloth Whoosh With Snap For Impact.wav",
 "Pro Sound Effect/38.Foley;Cloth,Nylon,Leather,Velcro,Zippers,Bag/32 Cloth Flaps, Shaking With Whoosh.wav",
 "Pro Sound Effect/38.Foley;Cloth,Nylon,Leather,Velcro,Zippers,Bag/49 Cloth,Canvass Jacket,On,Off.wav",
 "Pro Sound Effect/50.Designed Sounds/22 Skiing On Snow Steady With Maneuvers,Wind Whistle.wav",
 "音效/50.Designed Sounds/22 Skiing On Snow Steady With Maneuvers,Wind Whistle.wav",
]

def find_alt(b):
    cl = path2clus.get(b)
    if not cl: return None, None, "不在fullhash"
    h, paths = cl
    for m in paths:
        if m == b: continue
        q = resolve_q(dmap.get(m))
        if q: return q, h, "隔离区(%s)" % m
        if os.path.exists(m): return m, h, "原路径仍在"
        t = o.T(m)
        if t:
            p = os.path.join(LIB, t)
            if os.path.exists(p): return p, h, "现库(%s)" % t
    return None, h, "簇内无现存副本"

print("\n== 恢复源搜索 ==")
res = []
for b in LOST:
    src, h, why = find_alt(b)
    res.append({"lost": b, "src": src, "hash": h, "why": why})
    print("\nLOST:", b)
    print("   源:", src)
    print("   哈希:", (h or "")[:16], "|", why)

json.dump(res, open(os.path.join(ORG, "recovery_plan.json"), "w"), ensure_ascii=False, indent=1)
okn = sum(1 for r in res if r["src"])
print("\n可恢复: %d / %d" % (okn, len(res)))
