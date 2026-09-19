#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""库内小结石清单：空文件/脏字符/可疑可执行/垃圾快捷方式/残余压缩包"""
import os

LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
JUNK_EXT = {".exe", ".dll", ".lnk", ".url", ".db", ".sfk"}
ARC_EXT = {".rar", ".zip", ".7z", ".bin", ".iso", ".cue", ".tar", ".gz", ".bz2"}

zeros, dirty, execs, junk, arcs = [], [], [], [], []
for root, dirs, fns in os.walk(LIB):
    for fn in fns:
        p = os.path.join(root, fn)
        try: st = os.stat(p)
        except OSError: continue
        e = os.path.splitext(fn)[1].lower()
        rel = os.path.relpath(p, LIB)
        if st.st_size == 0:
            zeros.append(rel)
        if any(0xE000 <= ord(c) <= 0xF8FF for c in fn):
            dirty.append(rel)
        if e in (".exe", ".dll"):
            execs.append((rel, st.st_size))
        if e in JUNK_EXT or fn.lower() == ".ds_store":
            junk.append((rel, st.st_size))
        if e in ARC_EXT:
            arcs.append((rel, st.st_size))

print("== 空文件 (%d) ==" % len(zeros))
for x in zeros: print("   " + x)
print("\n== 脏名字符 (%d) ==" % len(dirty))
for x in dirty: print("   " + repr(x))
print("\n== 可执行 (.exe/.dll, %d) ==" % len(execs))
for x, s in execs: print("   %d B | %s" % (s, x))
print("\n== 快捷方式/垃圾 (.lnk/.url/.db/.sfk/.DS_Store, %d) ==" % len(junk))
for x, s in junk: print("   %d B | %s" % (s, x))
print("\n== 残余压缩包/镜像 (%d) ==" % len(arcs))
for x, s in sorted(arcs, key=lambda t: -t[1]): print("   %.2f MB | %s" % (s / 1e6, x))
print("\nDONE")
