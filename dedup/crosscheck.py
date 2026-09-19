#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""跨类核对：非音频文件是否与任何音频文件字节相同（+ 0 字节统计）。"""
import os, sqlite3, hashlib
LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
BASE = "/volume1/主目录/Hermes/read/Projects/sfx-browser"
DB = os.path.join(BASE, "data", "sfx.db")

def md5f(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b: break
            h.update(b)
    return h.hexdigest()

con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
audio_by_size = {}
idx = set()
for rel, size in con.execute("SELECT rel, size FROM files"):
    idx.add(rel)
    if size > 0: audio_by_size.setdefault(size, []).append(rel)
zero = 0; na = 0; cand = []
for root, dirs, files in os.walk(LIB):
    for fn in files:
        p = os.path.join(root, fn)
        try: st = os.stat(p)
        except OSError: continue
        if st.st_size == 0: zero += 1; continue
        rel = os.path.relpath(p, LIB)
        if rel in idx: continue
        na += 1
        if st.st_size in audio_by_size: cand.append((rel, st.st_size))
print("非音频 %d 个 | 0字节 %d 个 | 尺寸与音频撞车 %d 个" % (na, zero, len(cand)))
cache = {}; bad = []; checked = 0
for rel, size in cand:
    try: h1 = md5f(os.path.join(LIB, rel))
    except OSError: continue
    for a in audio_by_size[size]:
        if a not in cache:
            try: cache[a] = md5f(os.path.join(LIB, a))
            except OSError: cache[a] = None
        checked += 1
        if cache[a] == h1: bad.append((rel, a))
print("比对 %d 次 | 跨类真重复: %d 对" % (checked, len(bad)))
for b in bad[:10]: print("   ", b[0][:70], "==", b[1][:70])
print("CROSSCHECK-DONE")
