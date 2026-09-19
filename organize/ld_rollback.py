#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# LD 归一 回滚：ld_move_log.csv 逐行反向搬回
import os, csv, glob

AMP = chr(38)
BASE = [x for x in glob.glob('/volume1/*/Collection/*/') if AMP in x][0].rstrip('/')
LIB = BASE + '/音效'
ORG = '/volume1/主目录/Hermes/read/Projects/sfx-browser/organize'
TARGET = LIB + '/01_商业音效包/Lens Distortions'
JUNK = LIB + '/99_待整理/_小杂件_LD_20260919'

n = 0
with open(ORG + '/ld_move_log.csv', encoding='utf-8') as f:
    rd = csv.reader(f, delimiter='\t')
    next(rd)
    for src, dst, note in rd:
        if note == 'junk':
            cur = os.path.join(JUNK, dst[len('JUNK/'):])
        else:
            cur = os.path.join(TARGET, dst)
        if os.path.isfile(cur):
            os.makedirs(os.path.dirname(src), exist_ok=True)
            os.rename(cur, src)
            n += 1
print('rollback done: %d' % n)

# 清理空目录
for root in (TARGET, JUNK):
    if os.path.isdir(root):
        for r, dd, fs in os.walk(root, topdown=False):
            for d in dd:
                dp = os.path.join(r, d)
                try:
                    if not os.listdir(dp):
                        os.rmdir(dp)
                except OSError:
                    pass
        try:
            if not os.listdir(root):
                os.rmdir(root)
        except OSError:
            pass
print('cleanup done')
