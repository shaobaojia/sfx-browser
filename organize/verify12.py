#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""12个丢失文件·最终实证：全盘找字节副本（隔离区+现库+哈希记录）"""
import os, sys, csv, json, hashlib
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
need = {os.path.basename(x): x for x in LOST}

def md5f(p, limit=None):
    h = hashlib.md5()
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b: break
            h.update(b)
    return h.hexdigest()

# 1) 隔离区按名搜索
print("== 隔离区同名文件 ==")
qhits = {}
for root, dirs, fns in os.walk(QUAR):
    for fn in fns:
        if fn in need:
            p = os.path.join(root, fn)
            qhits.setdefault(fn, []).append(p)
            st = os.stat(p)
            print("  Q:", os.path.relpath(p, QUAR), "| %d B | md5=%s" % (st.st_size, md5f(p)))

# 2) 现库同名文件
print("\n== 现库同名文件（目标/冲突区版本）==")
lhits = {}
for root, dirs, fns in os.walk(LIB):
    for fn in fns:
        if fn in need:
            p = os.path.join(root, fn)
            lhits.setdefault(fn, []).append(p)
            st = os.stat(p)
            print("  L:", os.path.relpath(p, LIB), "| %d B | md5=%s" % (st.st_size, md5f(p)))

# 3) 哈希记录里搜（full_md5.csv）
print("\n== full_md5.csv 命中 ==")
ff = os.path.join(DED, "full_md5.csv")
with open(ff, encoding="utf-8-sig", errors="replace") as f:
    for line in f:
        for nm in need:
            if nm in line and "Pro Sound Effect" in line:
                print("  ", line.strip()[:200])
                break

# 4) 汇总
print("\n== 汇总 ==")
for b in LOST:
    nm = os.path.basename(b)
    q = len(qhits.get(nm, []))
    l = len(lhits.get(nm, []))
    print("  %s | 隔离区副本=%d 现库版本=%d" % (nm[:70], q, l))
