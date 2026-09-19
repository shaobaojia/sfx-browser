#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vol.2 轨名微调：' w- ' → ' with '（对齐 Vol.1 目录风格）"""
import os

V2 = "/volume1/主目录/Collection/素材&模板&音库/音效/01_商业音效包/[Sound.Ideas]The Metropolis Science Fiction Toolkit Vol.2"

n = 0
for f in sorted(os.listdir(V2)):
    if f.endswith(".wav") and " w- " in f:
        new = f.replace(" w- ", " with ")
        dst = os.path.join(V2, new)
        if os.path.exists(dst):
            print("目标已存在，跳过:", new); continue
        os.rename(os.path.join(V2, f), dst)
        print("  %r  ->  %r" % (f, new))
        n += 1
print("共调整 %d 个" % n)
print("DONE")
