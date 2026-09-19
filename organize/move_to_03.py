#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2：自解析基路径（零硬编码基路径），把 99_待整理/临时 项目件挪 03_项目素材"""
import os, glob, time

# ---- 1. 自解析：找所有 Collection 下含 '&' 的候选，取其中含有 01_/02_/03_/99_ 桶的孩子 ----
BASE = LIB = None
for x in sorted(glob.glob('/volume1/*/Collection/*/')):
    if '&' not in x:
        continue
    for sub in sorted(glob.glob(x + '*/')):
        try:
            ks = os.listdir(sub)
        except OSError:
            continue
        if sum(1 for k in ks if k[:3] in ('01_', '02_', '03_', '99_')) >= 3:
            BASE, LIB = x.rstrip('/'), sub.rstrip('/')
            break
    if LIB:
        break
assert LIB, "找不到音效库根"
print("BASE:", repr(BASE))
print("LIB :", repr(LIB))
print()

# ---- 2. 定位 SRC(99_*) 和 DST(03_*) ----
SRC = DST = None
for k in os.listdir(LIB):
    p = os.path.join(LIB, k)
    if os.path.isdir(p) and k.startswith('99_'):
        SRC = p
    if os.path.isdir(p) and k.startswith('03_'):
        DST = p
assert SRC and DST, (SRC, DST)
TMP = os.path.join(SRC, '临时')
print("TMP:", repr(TMP), os.path.isdir(TMP))
print("DST:", repr(DST), os.path.isdir(DST))
print()

names = ['腾格里-绿灯版音效', '参考音乐']
rows = []
for n in names:
    s = os.path.join(TMP, n)
    d = os.path.join(DST, n)
    s_ok, d_ok = os.path.isdir(s), os.path.isdir(d)
    if not s_ok and d_ok:
        print(".. 已在目标位（跳过）:", repr(n))
        rows.append([n, '-', '-', 'already', time.strftime('%F %T')])
        continue
    assert s_ok, "源不存在且目标也不存在: " + repr(n)
    assert not d_ok, "目标已存在: " + repr(d)
    cnt = sum(len(fs) for _, _, fs in os.walk(s))
    sz = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(s) for f in fs)
    os.rename(s, d)
    ok = os.path.isdir(d) and not os.path.exists(s)
    print(("✓ moved" if ok else "✗ FAILED"), repr(n), cnt, "files", sz, "B")
    rows.append([n, str(cnt), str(sz), 'ok' if ok else 'FAILED', time.strftime('%F %T')])

logp = os.path.join('/volume1/主目录/Hermes/read/Projects/sfx-browser/organize', 'to03_moved_20260919.log')
with open(logp, 'w', encoding='utf-8') as f:
    f.write("item\tfiles\tbytes\tstatus\ttime\n")
    for r in rows:
        f.write('\t'.join(r) + '\n')
print()
print("DST 现状:", sorted(os.listdir(DST)))
print("TMP 剩余子目录:", sorted(x for x in os.listdir(TMP) if os.path.isdir(os.path.join(TMP, x))))
