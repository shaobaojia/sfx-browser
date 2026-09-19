#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""狗/ 归位：τïù 子目录 79 文件提上一级；与原有 26 个逐字节比对（同内容→挪去_垃圾件, 不同→_2）"""
import os, csv, zlib, shutil

T = "/volume1/主目录/Collection/素材&模板&音库/音效/02_中文音效合集/BD音效库/附赠音效库（转场+撞击+音效+环境音）/音效/动物类/狗"
JUNK2 = "/volume1/主目录/Collection/素材&模板&音库/音效/99_待整理/_垃圾件/狗_重复解压"
ORG = "/volume1/主目录/Hermes/read/Projects/sfx-browser/organize"
LOG = os.path.join(ORG, "dog_fix_20260919.log")

subs = [n for n in os.listdir(T) if os.path.isdir(os.path.join(T, n))]
assert len(subs) == 1, "子目录数异常: %r" % subs
SUB = os.path.join(T, subs[0])
files = sorted(os.listdir(SUB))
print("要上提的文件: %d（来源子目录 %r）" % (len(files), subs[0]))

def crc_of(p):
    c = 0
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b: break
            c = zlib.crc32(b, c)
    return c & 0xFFFFFFFF

up = dup = ren = 0
rows = []
for n in files:
    src = os.path.join(SUB, n)
    dst = os.path.join(T, n)
    if not os.path.exists(dst):
        os.rename(src, dst); up += 1
        rows.append([n, "上提", ""])
        continue
    if os.path.getsize(dst) == os.path.getsize(src) and crc_of(dst) == crc_of(src):
        os.makedirs(JUNK2, exist_ok=True)
        target = os.path.join(JUNK2, n); k = 2
        while os.path.exists(target):
            base, ext = os.path.splitext(os.path.join(JUNK2, n))
            target = "%s_%d%s" % (base, k, ext); k += 1
        shutil.move(src, target)
        dup += 1
        rows.append([n, "重复(字节一致)→_垃圾件/狗_重复解压", ""])
    else:
        base, ext = os.path.splitext(dst); k = 2
        while os.path.exists("%s_%d%s" % (base, k, ext)): k += 1
        alt = "%s_%d%s" % (base, k, ext)
        os.rename(src, alt); ren += 1
        rows.append([n, "内容不同→另存", os.path.basename(alt)])

os.rmdir(SUB)
print("上提 %d | 重复挪走 %d | 另存 %d" % (up, dup, ren))

n_now = len([n for n in os.listdir(T) if os.path.isfile(os.path.join(T, n))])
print("狗/ 现有文件: %d" % n_now)

with open(LOG, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["文件", "处置", "备注"])
    w.writerows(rows)
with open(os.path.join(JUNK2, "说明.txt"), "w", encoding="utf-8") as f:
    f.write("这 26 个文件 = 狗.zip 解压时与 狗/ 原有文件字节级相同的副本（仅保留一份，副本挪此）。\n")
    f.write("如需还原：把本目录文件挪回 ../动物类/狗/ 即可。明细见 organize/dog_fix_20260919.log\n")
print("DONE")
