#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""狗.zip → 合并解压进 狗/（同名同内容跳过、重名不同内容 _2 后缀）+ 全成员核验 + sha256 后删包"""
import os, zipfile, zlib, hashlib, sys

BASE = "/volume1/主目录/Collection/素材&模板&音库/音效/02_中文音效合集/BD音效库/附赠音效库（转场+撞击+音效+环境音）/音效/动物类"
ZP = os.path.join(BASE, "狗.zip")
TGT = os.path.join(BASE, "狗")
ORG = "/volume1/主目录/Hermes/read/Projects/sfx-browser/organize"
LOG = os.path.join(ORG, "dog_unzip_20260919.log")

z = zipfile.ZipFile(ZP)
def fname(i):
    if i.flag_bits & 0x800:
        return i.filename
    try:
        return i.filename.encode("cp437").decode("gbk")
    except Exception:
        return i.filename
def skip(n):
    b = n.replace("\\", "/").split("/")[-1]
    return n.startswith("__MACOSX") or b == ".DS_Store" or b.startswith("._")
members = [i for i in z.infolist() if not i.is_dir() and not skip(fname(i))]
print("有效成员: %d（跳过 mac 垃圾）" % len(members))

os.makedirs(TGT, exist_ok=True)
pre = set(os.listdir(TGT)) if os.path.isdir(TGT) else set()
print("目标 狗/ 已有: %d 项 %s" % (len(pre), sorted(pre)[:8]))

def crc_of(p):
    c = 0
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b: break
            c = zlib.crc32(b, c)
    return c & 0xFFFFFFFF

added = same = renamed = 0
fail = []
for i in members:
    parts = fname(i).replace("\\", "/").split("/")
    sub = parts[1:] if parts[0] == "狗" else parts
    dest = os.path.join(TGT, *sub)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    data = z.read(i)
    if os.path.exists(dest):
        if os.path.getsize(dest) == i.file_size and crc_of(dest) == (i.CRC & 0xFFFFFFFF):
            same += 1; continue
        base, ext = os.path.splitext(dest); k = 2
        while os.path.exists("%s_%d%s" % (base, k, ext)): k += 1
        dest = "%s_%d%s" % (base, k, ext); renamed += 1
    with open(dest, "wb") as w:
        w.write(data)
    added += 1

# 全成员核验：名字精确或 _N 变体，字节 CRC 必须一致
for i in members:
    parts = fname(i).replace("\\", "/").split("/")
    sub = parts[1:] if parts[0] == "狗" else parts
    cand = os.path.join(TGT, *sub)
    pool = []
    if os.path.exists(cand): pool.append(cand)
    base, ext = os.path.splitext(cand); k = 2
    while True:
        alt = "%s_%d%s" % (base, k, ext)
        if os.path.exists(alt): pool.append(alt); k += 1
        else: break
    ok = any(os.path.getsize(p) == i.file_size and crc_of(p) == (i.CRC & 0xFFFFFFFF) for p in pool)
    if not ok:
        fail.append(fname(i))

print("加入 %d | 同名同内容跳过 %d | 重名改名 %d | 核验失败 %d" % (added, same, renamed, len(fail)))
if fail:
    for x in fail[:20]: print("  !! " + x)
    print("!! 核验失败，不删 zip"); sys.exit(1)
print("全成员核验通过 ✓")

h = hashlib.sha256()
with open(ZP, "rb") as f:
    while True:
        b = f.read(1 << 22)
        if not b: break
        h.update(b)
with open(LOG, "w", encoding="utf-8") as f:
    f.write("狗.zip 解压记录 2026-09-19\n")
    f.write("zip: %d B | sha256=%s\n" % (os.path.getsize(ZP), h.hexdigest()))
    f.write("成员 %d | 加入 %d | 跳过 %d | 改名 %d\n" % (len(members), added, same, renamed))
os.remove(ZP)
print("狗.zip sha256=%s" % h.hexdigest())
print("狗.zip 已删除")
print("DONE")
