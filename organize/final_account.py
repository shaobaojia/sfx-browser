#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""终审账目：只读。所有基路径 glob 自解析，避免长中文字符串硬编码。"""
import os, glob

BASE = [x for x in glob.glob('/volume1/*/Collection/*/') if '&' in x][0].rstrip('/')
LIB = None
for sub in sorted(glob.glob(BASE + '/*/')):
    try:
        ks = os.listdir(sub)
    except OSError:
        continue
    if sum(1 for k in ks if k[:3] in ('01_', '02_', '03_', '99_')) >= 3:
        LIB = sub.rstrip('/')
        break
assert LIB, 'lib not found'

print('BASE:', repr(BASE))
print('LIB :', repr(LIB))
print()

total = 0
sz = 0
for b in sorted(os.listdir(LIB)):
    p = os.path.join(LIB, b)
    if not os.path.isdir(p):
        continue
    n = 0
    for r, _, fs in os.walk(p):
        n += len(fs)
        for f in fs:
            try:
                sz += os.path.getsize(os.path.join(r, f))
            except OSError:
                pass
    total += n
    print('%s: %d' % (b, n))
print('TOTAL files:', total)
print('TOTAL bytes:', sz, '=', round(sz / 1024**3, 1), 'GiB')
print()

# 自校验：手打字符串 vs 真实
t = os.path.basename(BASE)
a = "素材&模板&音库"
b2 = "素材&模板&音库"
print('selfcheck: a==t:', a == t, '| b==t:', b2 == t)
if a != t:
    print(' a hex:', a.encode('utf-8').hex())
    print(' t hex:', t.encode('utf-8').hex())
print()

# 99_待整理 详情
c99 = os.path.join(LIB, [k for k in os.listdir(LIB) if k.startswith('99_')][0])
print('99 kids:', [repr(x) for x in sorted(os.listdir(c99))])
# 子目录计数（命名冲突等）
for k in sorted(os.listdir(c99)):
    kp = os.path.join(c99, k)
    if os.path.isdir(kp):
        n = sum(len(fs) for _, _, fs in os.walk(kp))
        print('   [%s] files: %d' % (k, n))

# 03 桶
c03 = os.path.join(LIB, [k for k in os.listdir(LIB) if k.startswith('03_')][0])
print()
print('03 kids:', [repr(x) for x in sorted(os.listdir(c03))])
