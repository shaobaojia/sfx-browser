#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""并库 r2 回滚：按 r2 日志把隔离件与归桶目录移回原位。--dry 先行。"""
import os, sys, glob

MODE = sys.argv[1] if len(sys.argv) > 1 else '--dry'
EXEC = (MODE == '--execute')
AMP = chr(38)
BASE = [x for x in glob.glob('/volume1/*/Collection/*/') if AMP in x][0].rstrip('/')
main = None
for name in sorted(os.listdir(BASE)):
    p = os.path.join(BASE, name)
    if not os.path.isdir(p):
        continue
    ks = os.listdir(p)
    if sum(1 for k in ks if k[:3] in ('01_', '02_', '03_', '99_')) >= 3:
        main = p
ORG = '/volume1/主目录/Hermes/read/Projects/sfx-browser/organize'
QUAR = os.path.join(BASE, '音效_去重待删_20260919_r2')

ops = []
with open(os.path.join(ORG, 'r2_quarantine_moved.csv'), encoding='utf-8') as f:
    next(f)
    for line in f:
        sib, rel, size, reason, mrel = line.rstrip('\n').split('\t')
        ops.append((os.path.join(QUAR, sib, rel), os.path.join(BASE, sib, rel)))
with open(os.path.join(ORG, 'r2_merge_moved.csv'), encoding='utf-8') as f:
    next(f)
    for line in f:
        sib, item, bucket, status = line.rstrip('\n').split('\t')
        ops.append((os.path.join(main, bucket, item), os.path.join(BASE, sib, item)))

n = 0
for src, dst in ops:
    if EXEC:
        if os.path.exists(src) and not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            os.rename(src, dst)
            n += 1
    else:
        n += 1
print('%s: 回滚操作 %d 项' % (MODE, n))
