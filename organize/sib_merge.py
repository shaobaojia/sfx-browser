#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""并库 r2：邻居 → 去重(隔离) → 归桶(01/02/04)。
用法: python3 sib_merge.py --dry   |   python3 sib_merge.py --execute
前缀以 '!' 结尾 = 精确匹配，否则前缀匹配。
"""
import os, sys, json, glob
from collections import defaultdict

MODE = sys.argv[1] if len(sys.argv) > 1 else '--dry'
EXEC = (MODE == '--execute')

AMP = chr(38)
BASE = [x for x in glob.glob('/volume1/*/Collection/*/') if AMP in x][0].rstrip('/')
main = None
sibs = {}
for name in sorted(os.listdir(BASE)):
    p = os.path.join(BASE, name)
    if not os.path.isdir(p):
        continue
    ks = os.listdir(p)
    if sum(1 for k in ks if k[:3] in ('01_', '02_', '03_', '99_')) >= 3:
        main = p
    elif '音' in name:
        sibs[name] = p
assert main and len(sibs) == 2

ORG = '/volume1/主目录/Hermes/read/Projects/sfx-browser/organize'
HASH = os.path.join(ORG, 'hash3_20260919')
QUAR = os.path.join(BASE, '音效_去重待删_20260919_r2')

meta = json.load(open(os.path.join(HASH, 'meta.json')))
sibnames = meta['sib_names']
key_of = {sibnames[0]: 'sib_1', sibnames[1]: 'sib_2'}

def load(key):
    rows = []
    with open(os.path.join(HASH, key + '.tsv'), encoding='utf-8') as f:
        for line in f:
            s, h, rel = line.rstrip('\n').split('\t', 2)
            rows.append((int(s), h, rel))
    return rows

main_map = defaultdict(list)
for s, h, rel in load('main'):
    main_map[(s, h)].append(rel)

# ---- 计算 ----
dups = []            # (sibname, rel, size, main_rel)
new_rows = []        # (sibname, size, md5, rel)
for name in sibs:
    for s, h, rel in load(key_of[name]):
        m = main_map.get((s, h))
        if m:
            dups.append((name, rel, s, m[0]))
        else:
            new_rows.append((name, s, h, rel))

groups = defaultdict(list)
for name, s, h, rel in new_rows:
    groups[(s, h)].append((name, rel))
excess = []          # (sibname, rel, size, reason)
for (s, h), lst in groups.items():
    if len(lst) > 1:
        keeper = min(lst, key=lambda t: (t[1].count('/'), len(t[1]), t[1]))
        for t in lst:
            if t != keeper:
                reason = 'dup_internal' if t[0] == keeper[0] else 'dup_cross'
                excess.append((t[0], t[1], s, reason))

# ---- 归桶计划 ----
MOVE_PLAN = [
    ('音乐&音效库', '190512', '02_中文音效合集'),
    ('音乐&音效库', 'Mechanicals', '01_商业音效包'),
    ('音乐&音效库', 'Medieval Weapons', '01_商业音效包'),
    ('音乐&音效库', '大气危险', '01_商业音效包'),
    ('音乐&音效库', '大气深沉1', '02_中文音效合集'),
    ('音乐&音效库', '大气深沉2', '02_中文音效合集'),
    ('音乐&音效库', '大气深沉3', '02_中文音效合集'),
    ('音乐&音效库', '大气深沉4', '02_中文音效合集'),
    ('音乐&音效库', '大气深沉5', '02_中文音效合集'),
    ('音乐&音效库', '大气深沉6', '02_中文音效合集'),
    ('音乐&音效库', '转场音效!', '02_中文音效合集'),
    ('音乐&音效库', '转场音效-329', '02_中文音效合集'),
    ('音乐&音效库', '190606', '04_音乐'),
    ('音乐&音效库', 'Multiply Sound@', '04_音乐'),
    ('音库', 'Brand X', '04_音乐'),
    ('音库', '原声', '04_音乐'),
]
SPLIT = ('音库', '原声', '超级音效', '02_中文音效合集')

lib_bucket = {b: os.path.join(main, b) for b in ('01_商业音效包', '02_中文音效合集', '04_音乐')}

# ---- 预检 ----
problems = []
for name, rel, s, mrel in dups:
    if not os.path.isfile(os.path.join(BASE, name, rel)):
        problems.append('dup 源缺失: %s/%s' % (name, rel))
    if not os.path.isfile(os.path.join(main, mrel)):
        problems.append('主库侧缺失: %s' % mrel)
for name, rel, s, reason in excess:
    if not os.path.isfile(os.path.join(BASE, name, rel)):
        problems.append('excess 源缺失: %s/%s' % (name, rel))

moves = []
for sibname, prefix, bucket in MOVE_PLAN:
    exact = prefix.endswith('!')
    q = prefix[:-1] if exact else prefix
    hits = [d for d in sorted(os.listdir(os.path.join(BASE, sibname)))
            if (d == q if exact else d.startswith(q))]
    if len(hits) != 1:
        problems.append('前缀 %r 在 %s 命中 %d 个: %s' % (prefix, sibname, len(hits), hits))
        continue
    item = hits[0]
    tgt = os.path.join(lib_bucket[bucket], item)
    if os.path.exists(tgt):
        problems.append('目标已存在: %s' % tgt)
    moved_rel = set(r for n2, r, _, _ in dups if n2 == sibname)
    moved_rel |= set(r for n2, r, _, _ in excess if n2 == sibname)
    n = 0
    b = 0
    for r, _, fs in os.walk(os.path.join(BASE, sibname, item)):
        for f in fs:
            fp = os.path.join(r, f)
            rel2 = os.path.relpath(fp, os.path.join(BASE, sibname))
            if rel2 in moved_rel:
                continue
            n += 1
            try:
                b += os.path.getsize(fp)
            except OSError:
                pass
    moves.append((sibname, item, bucket, n, b))

sp_item = None
sib0 = os.path.join(BASE, SPLIT[0])
cand = [d for d in sorted(os.listdir(sib0)) if d.startswith(SPLIT[1])]
if len(cand) == 1:
    sp_item = os.path.join(sib0, cand[0], SPLIT[2])
    if not os.path.isdir(sp_item):
        sp_item = None

# ---- 报告 ----
total_dup_b = sum(s for _, _, s, _ in dups)
total_exc_b = sum(s for _, _, s, _ in excess)
print('模式:', MODE)
print('重复(对主库): %d 件 / %.2f GiB' % (len(dups), total_dup_b / 1024**3))
print('多余(内部+跨邻居): %d 件 / %.2f GiB' % (len(excess), total_exc_b / 1024**3))
print('隔离区: %s' % QUAR)
print()
print('归桶计划:')
for sibname, item, bucket, n, b in moves:
    print('  %s: %s → %s  (%d 件 / %.1f MB 去重后)' % (sibname, item[:52], bucket, n, b / 1024**2))
print('  拆分:', SPLIT if sp_item else '(无 超级音效 子目录，跳过)')
print()
if problems:
    print('!!! 问题 %d 个:' % len(problems))
    for x in problems[:30]:
        print('   ', x)
    if EXEC:
        print('存在预检问题，拒绝执行。')
        sys.exit(1)

if not EXEC:
    print('--dry 完成（未动任何文件）。示例:')
    print('  重复件前 3:', [(r[:60], s) for _, r, s, _ in dups[:3]])
    print('  多余件前 3:', [(r[:60], s) for _, r, s, _ in excess[:3]])
    sys.exit(0)

# ---- 执行 ----
errs = 0
os.makedirs(QUAR, exist_ok=True)
qlog = open(os.path.join(ORG, 'r2_quarantine_moved.csv'), 'w', encoding='utf-8')
qlog.write('sib\trel\tsize\treason\tmain_rel\n')
def mv(src, dst):
    global errs
    try:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        os.rename(src, dst)
        return True
    except OSError as e:
        errs += 1
        print('!! move fail:', src, '->', dst, e)
        return False

mved = 0
for name, rel, s, mrel in dups:
    if mv(os.path.join(BASE, name, rel), os.path.join(QUAR, name, rel)):
        qlog.write('%s\t%s\t%d\tdup_main\t%s\n' % (name, rel, s, mrel))
        mved += 1
for name, rel, s, reason in excess:
    if mv(os.path.join(BASE, name, rel), os.path.join(QUAR, name, rel)):
        qlog.write('%s\t%s\t%d\t%s\t\n' % (name, rel, s, reason))
        mved += 1
qlog.close()
print('隔离完成: %d 件 (错误 %d)' % (mved, errs))

pruned = 0
for name in sibs:
    root = os.path.join(BASE, name)
    for r, ds, fs in os.walk(root, topdown=False):
        for d in ds:
            dp = os.path.join(r, d)
            try:
                if not os.listdir(dp):
                    os.rmdir(dp)
                    pruned += 1
            except OSError:
                pass
print('清理空目录: %d' % pruned)

os.makedirs(lib_bucket['04_音乐'], exist_ok=True)
mlog = open(os.path.join(ORG, 'r2_merge_moved.csv'), 'w', encoding='utf-8')
mlog.write('sib\titem\tbucket\tstatus\n')
if sp_item:
    d = os.path.join(lib_bucket[SPLIT[3]], SPLIT[2])
    if not os.path.exists(d):
        os.rename(sp_item, d)
        print('拆分移动: %s/超级音效 → %s' % (SPLIT[0], SPLIT[3]))

for sibname, item, bucket, n, b in moves:
    src = os.path.join(BASE, sibname, item)
    dst = os.path.join(lib_bucket[bucket], item)
    if mv(src, dst):
        mlog.write('%s\t%s\t%s\tok\n' % (sibname, item, bucket))
        print('移动: %s → %s' % (item[:52], bucket))
mlog.close()

for name in sibs:
    root = os.path.join(BASE, name)
    if os.path.isdir(root):
        rest = os.listdir(root)
        if not rest:
            os.rmdir(root)
            print('空目录已移除: %s' % name)
        else:
            print('!! %s 仍剩 %d 项: %s' % (name, len(rest), rest[:10]))

with open(os.path.join(QUAR, '说明.txt'), 'w', encoding='utf-8') as f:
    f.write('本隔离区为 2026-09-19 并库去重的副产品：与主库逐字节重复的邻居副本（dup_main）、'
            '邻居内部/跨邻居多余副本（dup_internal/dup_cross）。\n只移不删；清单见仓库 organize/r2_quarantine_moved.csv，'
            '回滚脚本 r2_rollback.py。\n')
print('ALLDONE (errs=%d)' % errs)
