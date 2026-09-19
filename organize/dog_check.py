#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""狗/ 目录现状核查：顶层 repr、完整清单、大小和 mtime（区分原有 vs 新增）"""
import os, time

BASE = "/volume1/主目录/Collection/素材&模板&音库/音效/02_中文音效合集/BD音效库/附赠音效库（转场+撞击+音效+环境音）/音效/动物类"

print("== 动物类 顶层（repr 找隐藏字符同名目录）==")
for n in sorted(os.listdir(BASE)):
    print("  ", repr(n))

T = os.path.join(BASE, "狗")
items = sorted(os.listdir(T))
print("== 狗/ 条目数: %d ==" % len(items))
for n in items:
    p = os.path.join(T, n)
    if os.path.isdir(p):
        print("DIR  %r  -> %d 项" % (n, len(os.listdir(p))))
    else:
        st = os.stat(p)
        print("%10d  %s  %r" % (st.st_size, time.strftime("%m-%d %H:%M", time.localtime(st.st_mtime)), n))
print("DONE")
