#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""候选件分布与体量测算 + 主库目标侧统计（只读，不哈希）"""
import os, glob, sqlite3
from collections import Counter, defaultdict

AMP = chr(38)
BASE = [x for x in glob.glob('/volume1/*/Collection/*/') if AMP in x][0].rstrip('/')
main = None
sibs = []
for name in sorted(os.listdir(BASE)):
    p = os.path.join(BASE, name)
    if not os.path.isdir(p):
        continue
    ks = os.listdir(p)
    if sum(1 for k in ks if k[:3] in ('01_', '02_', '03_', '99_')) >= 3:
        main = p
    elif '音' in name:
        sibs.append((name, p))

# 候选清单（上一步已存）
cand = defaultdict(list)
with open('/volume1/主目录/Hermes/read/Projects/sfx-browser/organize/sib_dup_candidates_20260919.txt', encoding='utf-8') as f:
    cur = None
    for line in f:
        line = line.rstrip('\n')
        if line.startswith('### '):
            cur = line[4:].split(' (')[0]
            continue
        if not line:
            continue
        sz, rp = line.split('\t', 1)
        cand[cur].append((rp, int(sz)))

# 每库候选的 顶层目录分布 / 体量 / NEW 对比
for name, p in sibs:
    rows = cand[name]
    tot_b = sum(s for _, s in rows)
    print('=' * 72)
    print('【%s】候选 %d 件 / %.1f GiB' % (name, len(rows), tot_b / 1024**3))
    per = Counter()
    perb = Counter()
    for rp, s in rows:
        top = rp.split('/', 1)[0]
        per[top] += 1
        perb[top] += s
    for t, n in per.most_common(20):
        print('   %-52s %6d  %8.1f MB' % (t[:50], n, perb[t] / 1024**2))
    # 每库总量对照
    alln = 0
    print('   —— 候选占比: %d 件中 %d 为嫌疑' % (0, len(rows)))

# 主库目标侧：candidates 的 (name,size) 对应主库文件数与体量
db = '/volume1/主目录/Hermes/read/Projects/sfx-browser/data/sfx.db'
con = sqlite3.connect('file:%s?mode=ro' % db, uri=True)
cur = con.cursor()
idx = defaultdict(list)
for rel, nm, sz in cur.execute('select rel, name, size from files'):
    idx[(nm.lower(), sz)].append(rel)

targets = set()
tbytes = 0
pairs = 0
for name, p in sibs:
    for rp, s in cand[name]:
        key = (os.path.basename(rp).lower(), s)
        m = idx.get(key, [])
        pairs += 1
        for r in m:
            if r not in targets:
                targets.add(r)
                tbytes += s  # 同 size
print('=' * 72)
print('主库侧目标: %d 个候选键命中主库; 需哈希主库文件 %d 个 / 约 %.1f GiB' % (
    sum(1 for name, _ in sibs for _ in cand[name] if idx.get((os.path.basename(_[0]).lower(), _[1]))),
    len(targets), tbytes / 1024**3))

# 多命中情况
multi = 0
for name, p in sibs:
    for rp, s in cand[name]:
        if len(idx.get((os.path.basename(rp).lower(), s), [])) > 1:
            multi += 1
print('一对多（主库同一 name+size 多处）的候选数:', multi)
print()
tot_sib_b = sum(s for name, _ in sibs for _, s in cand[name])
print('合计需哈希: 邻居侧 %.1f GiB + 主库侧 %.1f GiB ≈ %.1f GiB' % (
    tot_sib_b / 1024**3, tbytes / 1024**3, (tot_sib_b + tbytes) / 1024**3))
