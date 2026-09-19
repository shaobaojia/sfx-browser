#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
def sub(p, n=25):
    try:
        xs = sorted(os.listdir(os.path.join(LIB, p)))
    except OSError as e:
        return "ERR " + str(e)
    more = (" …(%d总)" % len(xs)) if len(xs) > n else ""
    return " ｜ ".join(xs[:n]) + more
print("== 音效/音效 顶层 =="); print(sub("音效/音效", 30))
print("== 音效/音效/BD音效库 顶层 =="); print(sub("音效/音效/BD音效库", 25))
print("== 音效素材1 顶层 =="); print(sub("音效/音效素材1", 30))
print("== PSF 子目录 =="); print(sub("Pro Sound Effect", 60))
print("== US01 样例 =="); print(sub("US01", 10))
print("== wb04 样例 =="); print(sub("wb04", 10))
print("== [WHO01] 样例 =="); print(sub("[WHO01]", 10))
print("== Wind 顶层 =="); print(sub("Wind", 30))
print("== 预告 顶层 =="); print(sub("预告", 30))
print("== 临时 顶层 =="); print(sub("临时", 30))
def rels(base):
    S = set()
    for root, dirs, fs in os.walk(os.path.join(LIB, base)):
        for f in fs:
            S.add(os.path.relpath(os.path.join(root, f), os.path.join(LIB, base)))
    return S
print("== 多版本对重叠 ==")
for a, b in [("卡通（华纳兄弟电影）", "卡通（华纳兄弟电影） (2)"),
             ("卡通（华纳兄弟电影）", "卡通（华纳兄弟电影） (3)"),
             ("脚步声", "脚步声02"), ("飞机", "飞机02"), ("电影级音效", "电影音效")]:
    try:
        ra, rb = rels(a), rels(b)
        print("  %s vs %s: A=%d B=%d 同名交集=%d" % (a[:18], b[:18], len(ra), len(rb), len(ra & rb)))
    except OSError as e:
        print("  ERR", a, b, e)
print("== 全库 >500MB 文件 TOP20 ==")
big = []
for root, dirs, fs in os.walk(LIB):
    for f in fs:
        p = os.path.join(root, f)
        try: s = os.path.getsize(p)
        except OSError: continue
        if s > 500 * 2**20: big.append((os.path.relpath(p, LIB), s))
for p, s in sorted(big, key=lambda x: -x[1])[:20]:
    print("  %8.2f GB ｜ %s" % (s / 2**30, p[:110]))
print("大文件合计:", len(big), "个")
