#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""哈希完成后：三根比对分析 → 重复清单 + 新增构成（只读）"""
import os, json
from collections import defaultdict, Counter

OUT = '/volume1/主目录/Hermes/read/Projects/sfx-browser/organize/hash3_20260919'
ORG = '/volume1/主目录/Hermes/read/Projects/sfx-browser/organize'

def load(key):
    rows = []
    with open(os.path.join(OUT, key + '.tsv'), encoding='utf-8') as f:
        for line in f:
            s, h, rel = line.rstrip('\n').split('\t', 2)
            rows.append((int(s), h, rel))
    return rows

print('加载 main ...')
main = load('main')
main_map = defaultdict(list)
for s, h, rel in main:
    main_map[(s, h)].append(rel)
print('main:', len(main), 'files,', len(main_map), 'unique (size,md5)')

dup_csv = open(os.path.join(ORG, 'r2_sib_vs_main_dups.csv'), 'w', encoding='utf-8')
int_csv = open(os.path.join(ORG, 'r2_sib_internal_dups.csv'), 'w', encoding='utf-8')

new_all = {}
for key in ('sib_1', 'sib_2'):
    rows = load(key)
    dup = []
    new = []
    for s, h, rel in rows:
        m = main_map.get((s, h))
        if m:
            dup.append((s, h, rel, m))
        else:
            new.append((s, h, rel))
    # internal dups
    groups = defaultdict(list)
    for s, h, rel in new:
        groups[(s, h)].append(rel)
    internal = [(s, h, rels) for (s, h), rels in groups.items() if len(rels) > 1]
    excess = sum(len(rels) - 1 for _, _, rels in internal)
    # 罗列
    for s, h, rel, m in dup:
        dup_csv.write('%s\t%d\t%s\t%s\t%s\n' % (key, s, rel, m[0], '|'.join(m[:5])))
    for s, h, rels in internal:
        int_csv.write('%s\t%d\t%s\t%s\n' % (key, s, '|'.join(rels), h))
    # 新增按顶层项统计
    top_cnt = Counter(); top_by = Counter()
    for s, h, rel in new:
        t = rel.split('/', 1)[0] if '/' in rel else '(root)'
        top_cnt[t] += 1; top_by[t] += s
    new_all[key] = new
    print()
    print('== [%s] 总 %d | 与主库真重复 %d (%.2f GiB) | 自身内部重复组 %d (多余 %d 件) | 真新增 %d (%.2f GiB)' % (
        key, len(rows), len(dup), sum(x[0] for x in dup) / 1024**3,
        len(internal), excess, len(new) - sum(1 for _, _, rels in internal for _ in rels[1:]),
        sum(s for s, _, _ in new) / 1024**3))
    print('  新增构成（前 20 项）:')
    for t, n in top_cnt.most_common(20):
        print('    %-56s %6d  %8.1f MB' % (t[:54], n, top_by[t] / 1024**2))

dup_csv.close(); int_csv.close()

# 跨邻居
a = set((s, h) for s, h, _ in new_all.get('sib_1', []))
b = set((s, h) for s, h, _ in new_all.get('sib_2', []))
print()
print('跨邻居真重复 (size,md5) 交集:', len(a & b))

# 预筛 vs 真重复 对账：同名同大小但内容不同
cand_rel = set()
with open(os.path.join(ORG, 'sib_dup_candidates_20260919.txt'), encoding='utf-8') as f:
    cur = None
    for line in f:
        line = line.rstrip('\n')
        if line.startswith('### '):
            cur = line[4:].split(' (')[0]
            continue
        if line and cur:
            sz, rp = line.split('\t', 1)
            cand_rel.add((cur, rp))
sib_md5 = {}
for key in ('sib_1', 'sib_2'):
    for s, h, rel in (load(key)):
        sib_md5[(key, rel)] = (s, h)
# 找同名同大小但 md5 不同的
false_pos = 0
for (cur, rp) in sorted(cand_rel):
    key = 'sib_1' if '音乐' in cur else 'sib_2'
    v = sib_md5.get((key, rp))
    if not v:
        continue
    s, h = v
    if (s, h) not in main_map:
        false_pos += 1
        if false_pos <= 15:
            print('  同名同大小但内容不同:', cur, '|', rp[:100])
print()
print('预筛候选 %d 件中，内容不同（假候选）:', false_pos)
print('DONE')
