#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""4桶顶层内容体检：每项 文件数/大小/类型分布/非音频/空文件/脏字符/样例"""
import os
from collections import Counter

LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
BUCKETS = ["01_商业音效包", "02_中文音效合集", "03_项目素材", "99_待整理"]
AUDIO_EXT = {".wav", ".mp3", ".aif", ".aiff", ".flac", ".ogg", ".m4a", ".aac", ".wma",
             ".opus", ".caf", ".ape", ".wv", ".aifc", ".mp2", ".mpga", ".ac3", ".dts"}
SUSPECT = {".exe", ".bat", ".cmd", ".scr", ".lnk", ".vbs", ".js", ".dll", ".msi", ".jar", ".apk", ".sh"}

def dirty(fn):
    return any(0xE000 <= ord(c) <= 0xF8FF for c in fn)

for b in BUCKETS:
    print(); print("################ %s" % b)
    bp = os.path.join(LIB, b)
    for item in sorted(os.listdir(bp)):
        ip = os.path.join(bp, item)
        if os.path.isfile(ip):
            print("  [文件] %s | %d B" % (item, os.path.getsize(ip)))
            continue
        n = size = zeros = dirtyn = 0
        ext = Counter(); nona = Counter(); suspect = []
        samples = []; subs = None
        for root, dirs, fns in os.walk(ip):
            if subs is None:
                subs = sorted(dirs)[:10] or sorted(fns)[:10]
            for fn in fns:
                p = os.path.join(root, fn)
                try: st = os.stat(p)
                except OSError: continue
                n += 1; size += st.st_size
                e = os.path.splitext(fn)[1].lower()
                ext[e] += 1
                if st.st_size == 0: zeros += 1
                if e not in AUDIO_EXT: nona[e] += 1
                if e in SUSPECT: suspect.append(p)
                if dirty(fn): dirtyn += 1
                if len(samples) < 3: samples.append(os.path.relpath(p, ip))
        print("  ● %s | %d 件 | %.2f GB" % (item, n, size / 1e9))
        print("      类型: %s" % ", ".join("%s×%d" % (k or "(无后缀)", v) for k, v in ext.most_common(6)))
        na = sum(nona.values())
        if na:
            print("      非音频 %d: %s" % (na, ", ".join("%s×%d" % (k, v) for k, v in nona.most_common(6))))
        flags = []
        if zeros: flags.append("空文件×%d" % zeros)
        if dirtyn: flags.append("脏名字符×%d" % dirtyn)
        if suspect: flags.append("可疑可执行×%d" % len(suspect))
        if flags: print("      ⚠️ %s" % " | ".join(flags))
        print("      内层: %s" % " / ".join(subs))
        print("      样例: %s" % " | ".join(samples))
        for p in suspect[:5]:
            print("      !! " + p)
print()
print("DONE")
