#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""尽职调查：在回收站里按名搜12件损失文件的老副本"""
import os
QUAR = "/volume1/主目录/#recycle"
NAMES = [
 "63 Two Single Body Falls On Gravel",
 "15 Wooden Bat Drops Onto Dirt Surface",
 "48 Very Low Frequency",
 "49 Avalanche Rumble With Rocks",
 "46 Sword ; Single Swish",
 "85 Toilet Paper From Roll",
 "06 Cloth,Grabs With Heavy",
 "28 Cloth Whoosh With Snap",
 "32 Cloth Flaps, Shaking",
 "49 Cloth,Canvass Jacket",
 "22 Skiing On Snow Steady",
]
hits = {n: [] for n in NAMES}
cnt = 0
for root, dirs, fns in os.walk(QUAR):
    cnt += len(fns)
    for fn in fns:
        for n in NAMES:
            if n in fn:
                p = os.path.join(root, fn)
                try: sz = os.path.getsize(p)
                except OSError: sz = -1
                hits[n].append((p, sz))
print("回收站文件总数:", cnt)
for n in NAMES:
    hs = hits[n]
    print("\n== %s : %d 个 ==" % (n, len(hs)))
    for p, sz in hs[:8]:
        print("   %d B | %s" % (sz, p))
print("\nDONE")
