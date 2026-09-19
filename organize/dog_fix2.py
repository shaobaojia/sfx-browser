#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""狗/ 深度归位2：mojibake 名还原真实中文名（cp437→utf-8），再与既有文件去重"""
import os, zlib, shutil, csv

T = "/volume1/主目录/Collection/素材&模板&音库/音效/02_中文音效合集/BD音效库/附赠音效库（转场+撞击+音效+环境音）/音效/动物类/狗"
JUNK2 = "/volume1/主目录/Collection/素材&模板&音库/音效/99_待整理/_垃圾件/狗_重复解压"
ORG = "/volume1/主目录/Hermes/read/Projects/sfx-browser/organize"
LOG = os.path.join(ORG, "dog_fix2_20260919.log")

def normalize(n):
    try:
        return n.encode("cp437").decode("utf-8")
    except Exception:
        return n

def crc_of(p):
    c = 0
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b: break
            c = zlib.crc32(b, c)
    return c & 0xFFFFFFFF

items = sorted(n for n in os.listdir(T) if os.path.isfile(os.path.join(T, n)))
moji = [n for n in items if normalize(n) != n]
print("总文件 %d | mojibake 名 %d 个:" % (len(items), len(moji)))
for n in moji:
    print("  %r  ->  %r" % (n, normalize(n)))

rows = []
fixed = dupm = 0
for n in moji:
    src = os.path.join(T, n)
    real = normalize(n)
    dst = os.path.join(T, real)
    if os.path.exists(dst):
        if os.path.getsize(dst) == os.path.getsize(src) and crc_of(dst) == crc_of(src):
            os.makedirs(JUNK2, exist_ok=True)
            tgt = os.path.join(JUNK2, real); k = 2
            while os.path.exists(tgt):
                base, ext = os.path.splitext(os.path.join(JUNK2, real))
                tgt = "%s_%d%s" % (base, k, ext); k += 1
            shutil.move(src, tgt); dupm += 1
            rows.append([n, real, "重复(字节一致)→_垃圾件"])
        else:
            base, ext = os.path.splitext(dst); k = 2
            while os.path.exists("%s_%d%s" % (base, k, ext)): k += 1
            alt = "%s_%d%s" % (base, k, ext)
            os.rename(src, alt); rows.append([n, os.path.basename(alt), "内容不同→另存"])
    else:
        os.rename(src, dst); fixed += 1
        rows.append([n, real, "还原改名"])

n_now = len([n for n in os.listdir(T) if os.path.isfile(os.path.join(T, n))])
print("还原改名 %d | 重复挪走 %d | 狗/ 现有文件 %d" % (fixed, dupm, n_now))

# 终检：还有没有 cp437 可编码的非 ASCII 名（可疑残留）
sus = []
for n in os.listdir(T):
    try:
        if any(c > 127 for c in n.encode("cp437")):
            sus.append(n)
    except Exception:
        pass
print("可疑残留:", sus if sus else "无")

with open(LOG, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["原文件名", "新文件名/真名", "处置"])
    w.writerows(rows)
print("DONE")
