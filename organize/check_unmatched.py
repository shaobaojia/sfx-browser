#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查未匹配文件的顶层名字（带 repr 显示隐藏字符）"""
import os, sys
sys.path.insert(0, "/volume1/主目录/Hermes/read/Projects/sfx-browser/organize")
import organize_execute as o
from collections import Counter

c = Counter(); samples = {}
for root, dirs, fns in os.walk(o.LIB):
    for fn in fns:
        rel = os.path.relpath(os.path.join(root, fn), o.LIB)
        if o.T(rel) is None:
            top = rel.split("/")[0]
            c[top] += 1
            if top not in samples: samples[top] = rel

print("未匹配分组数:", len(c), " 文件总数:", sum(c.values()))
for k, v in c.most_common():
    print(v, repr(k))
    print("   e.g.", repr(samples[k][:180]))
    # 逐段排查第二段
    s = samples[k]
    segs = s.split("/")
    if len(segs) > 1:
        print("   seg1:", repr(segs[1]))
