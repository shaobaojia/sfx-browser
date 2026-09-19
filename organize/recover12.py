#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""12个丢失文件·数学求解 v2：md5 → 全盘现存副本定位（哈希记录+隔离区+现库三方交叉）"""
import os, sys, csv, json, hashlib
from collections import defaultdict
sys.path.insert(0, "/volume1/主目录/Hermes/read/Projects/sfx-browser/organize")
import organize_execute as o
LIB = o.LIB; ORG = o.ORG
DED = "/volume1/主目录/Hermes/read/Projects/sfx-browser/dedup"
QUAR = "/volume1/主目录/Collection/素材&模板&音库/音效_去重待删_20260919"

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

def md5f(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b: break
            h.update(b)
    return h.hexdigest()

# 1) full_md5.csv
fm = {}; md5map = defaultdict(list)
with open(os.path.join(DED, "full_md5.csv"), encoding="utf-8-sig", errors="replace") as f:
    for row in csv.reader(f):
        if len(row) >= 3 and len(row[-1]) == 32:
            p = ",".join(row[:-2]) if len(row) > 3 else row[0]
            fm[p] = row[-1]; md5map[row[-1]].append(p)
print("full_md5 记录:", len(fm))

# 2) 隔离区记录
movedset = set()
with open(os.path.join(DED, "moved.csv"), encoding="utf-8-sig", errors="replace") as f:
    rd = csv.reader(f)
    for i, row in enumerate(rd):
        if i == 0: continue
        movedset.add(row[0])
print("隔离区记录:", len(movedset))

def where_now(p):
    out = []
    if p in movedset:
        q = os.path.join(QUAR, p)
        if os.path.exists(q): out.append(("Q", q))
    t = o.T(p)
    if t:
        cp = os.path.join(LIB, t)
        if os.path.exists(cp): out.append(("LIB", cp))
    return out

print("\n== 逐文件求解 ==")
results = []
for B in LOST:
    m = fm.get(B)
    print("\nLOST:", B)
    if not m:
        base = os.path.basename(B)
        near = [(k, v) for k, v in fm.items() if k.endswith(base) and "/" not in k.replace("音效/", "", 1)]
        allnear = [(k, v) for k, v in fm.items() if k.endswith(base)]
        print("   x 无精确哈希记录 → 内容孤本（未被哈希过）")
        print("   同名其它记录数:", len(allnear))
        for k, v in allnear[:6]: print("      ~", k[:100], v[:12])
        results.append({"lost": B, "md5": None, "sources": [], "verdict": "no-record"})
        continue
    print("   md5:", m)
    members = md5map[m]
    print("   同 md5 路径数:", len(members))
    srcs = []
    for p in members:
        if p == B: continue
        for tag, path in where_now(p):
            srcs.append({"from": p, "at": tag, "path": path})
            print("   + 副本:", tag, "<-", p[:110])
    verdict = "recoverable" if srcs else "unique-lost"
    if srcs:
        # 验证首个源的真身 md5
        v = md5f(srcs[0]["path"])
        ok = (v == m)
        print("   ✓ 源校验: md5", "一致" if ok else "不一致!! %s" % v)
        if not ok: verdict = "verify-fail"
    results.append({"lost": B, "md5": m, "sources": srcs, "verdict": verdict})

json.dump(results, open(os.path.join(ORG, "recover_sources.json"), "w"), ensure_ascii=False, indent=1)
from collections import Counter
c = Counter(r["verdict"] for r in results)
print("\n== 汇总 ==")
for k, v in c.items(): print("  ", k, v)
