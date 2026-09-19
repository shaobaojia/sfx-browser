#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""原始压缩包删除：先记录 sha256/大小/mtime，再删除，最后验证"""
import os, hashlib, datetime, shutil

Z = "/volume1/主目录/Collection/素材&模板&音库/音效/99_待整理/_原始压缩包"
ORG = "/volume1/主目录/Hermes/read/Projects/sfx-browser/organize"
LOG = os.path.join(ORG, "zip_deleted_20260919.log")

files = sorted(fn for fn in os.listdir(Z) if os.path.isfile(os.path.join(Z, fn)))
print("待删 %d 个文件" % len(files), flush=True)

recs = []
for fn in files:
    p = os.path.join(Z, fn)
    st = os.stat(p)
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 22)
            if not b: break
            h.update(b)
    rec = "%s | %d B | mtime %s | sha256=%s" % (
        fn, st.st_size,
        datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M"),
        h.hexdigest())
    recs.append(rec)
    print("  已记录: " + rec, flush=True)

with open(LOG, "a", encoding="utf-8") as f:
    f.write("== 删除记录 %s ==\n" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    f.write("验收结论: 2914 个成员 100% 在库（2864 字节级 + 50 音频级；详见 原始压缩包验收报告_2026-09-19.md）\n")
    for r in recs: f.write(r + "\n")
    f.write("----------\n")
print("记录已写入 %s" % LOG, flush=True)

for fn in files:
    os.remove(os.path.join(Z, fn))
    print("  已删: " + fn, flush=True)

rest = os.listdir(Z)
print("删除后剩余: %r" % rest, flush=True)
if not rest:
    os.rmdir(Z)
    print("空目录已移除: _原始压缩包/", flush=True)

if os.path.isdir("/tmp/zipcheck"):
    shutil.rmtree("/tmp/zipcheck")
    print("临时比对文件已清理 /tmp/zipcheck", flush=True)
print("DONE")
