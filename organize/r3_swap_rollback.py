#!/usr/bin/env python3
# r3 回滚：Multiply Sound 对换撤销（搬回→隔离区，对换出→01）
# 用法：python3 r3_swap_rollback.py
import csv, os, glob

AMP = chr(38)
BASE = [x for x in glob.glob('/volume1/*/Collection/*/') if AMP in x][0].rstrip('/')
LIB = BASE + '/音效'
QUAR = BASE + '/音效_去重待删_20260919_r2'
ORG = '/volume1/主目录/Hermes/read/Projects/sfx-browser/organize'
QSIB = '音乐' + AMP + '音效库'
DEST04 = LIB + '/04_音乐'
OUTROOT = QUAR + '/主库旧份对换/Multiply Sound Film Score Bundle'
BUNDLE = LIB + '/01_商业音效包/Multiply Sound Film Score Bundle'

n = m = 0
with open(ORG + '/r3_swap_restore.csv', encoding='utf-8') as f:
    rd = csv.reader(f, delimiter='\t')
    next(rd)
    for rel, size in rd:
        src = os.path.join(DEST04, rel)
        dst = os.path.join(QUAR, QSIB, rel)
        if os.path.isfile(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            os.rename(src, dst)
            n += 1

with open(ORG + '/r3_swap_out.csv', encoding='utf-8') as f:
    rd = csv.reader(f, delimiter='\t')
    next(rd)
    for rel, size in rd:
        src = os.path.join(OUTROOT, rel)
        dst = os.path.join(BUNDLE, rel)
        if os.path.isfile(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            os.rename(src, dst)
            m += 1

print('rollback done: %d 归还隔离区 / %d 归还 01' % (n, m))
