#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""邻居目录体检 + 对主库同名同大小预筛（只读）"""
import os, glob, sqlite3, json
from collections import Counter

AMP = chr(38)  # '&'
BASE = [x for x in glob.glob('/volume1/*/Collection/*/') if AMP in x][0].rstrip('/')
main = None
sibs = []
for name in sorted(os.listdir(BASE)):
    p = os.path.join(BASE, name)
    if not os.path.isdir(p):
        continue
    try:
        ks = os.listdir(p)
    except OSError:
        continue
    if sum(1 for k in ks if k[:3] in ('01_', '02_', '03_', '99_')) >= 3:
        main = p
    elif '音' in name:
        sibs.append((name, p))

print('MAIN:', repr(main))
print('音频邻居:', [n for n, _ in sibs])
print()

sib_files = {}
for name, p in sibs:
    tot = 0
    byt = 0
    ext = Counter()
    items = []
    for it in sorted(os.listdir(p)):
        ip = os.path.join(p, it)
        if os.path.isdir(ip):
            n = 0
            b = 0
            for r, _, fs in os.walk(ip):
                n += len(fs)
                for f in fs:
                    try:
                        b += os.path.getsize(os.path.join(r, f))
                    except OSError:
                        pass
            items.append((it, n, b))
            tot += n
            byt += b
        else:
            try:
                b = os.path.getsize(ip)
            except OSError:
                b = 0
            items.append((it, 1, b))
            tot += 1
            byt += b
    for r, _, fs in os.walk(p):
        for f in fs:
            e = f.rsplit('.', 1)[-1].lower() if '.' in f else '(none)'
            ext[e] += 1
    sample = []
    for r, _, fs in os.walk(p):
        for f in fs:
            sample.append(os.path.relpath(os.path.join(r, f), p))
    sib_files[name] = sample
    print('=' * 72)
    print('【%s】 files=%d  %.1f GiB' % (name, tot, byt / 1024**3))
    print('ext:', ext.most_common(12))
    print('top items (%d):' % len(items))
    for it, n, b in items[:60]:
        print('   %-58s %6d  %8.1f MB' % (it[:56], n, b / 1024**2))
    print('--- 样例 20 条 ---')
    for s in sample[:20]:
        print('   ·', s)
    print()

print('=' * 72)
print('== 主库索引（sfx.db）加载 + 同名同大小预筛 ==')
db = '/volume1/主目录/Hermes/read/Projects/sfx-browser/data/sfx.db'
con = sqlite3.connect('file:%s?mode=ro' % db, uri=True)
cur = con.cursor()
cols = [c[1] for c in cur.execute('pragma table_info(files)').fetchall()]
print('files 列:', cols)
main_pairs = Counter()
for n_, s_ in cur.execute('select name, size from files'):
    main_pairs[(n_.lower(), s_)] += 1
print('主库 (name,size) 对:', len(main_pairs), '总条目:', sum(main_pairs.values()))
print()

cand_all = {}
for name, p in sibs:
    cands = []
    for fp in sib_files[name]:
        ap = os.path.join(p, fp)
        try:
            sz = os.path.getsize(ap)
        except OSError:
            continue
        if (os.path.basename(fp).lower(), sz) in main_pairs:
            cands.append((fp, sz))
    cand_all[name] = cands
    print('【%s】→ 与主库同名同大小候选: %d 件' % (name, len(cands)))
    for c in cands[:20]:
        print('    %8d  %s' % (c[1], c[0]))
    print()

if len(sibs) == 2:
    a = set((os.path.basename(x).lower(), os.path.getsize(os.path.join(sibs[0][1], x))) for x in sib_files[sibs[0][0]])
    b = set((os.path.basename(x).lower(), os.path.getsize(os.path.join(sibs[1][1], x))) for x in sib_files[sibs[1][0]])
    inter = a | b
    print('两邻居之间 同名同大小交集:', len(a & b))

outp = '/volume1/主目录/Hermes/read/Projects/sfx-browser/organize/sib_dup_candidates_20260919.txt'
with open(outp, 'w', encoding='utf-8') as f:
    for name, cands in cand_all.items():
        f.write('### %s (%d)\n' % (name, len(cands)))
        for fp, sz in cands:
            f.write('%d\t%s\n' % (sz, fp))
print('候选清单已存:', outp)

fhp = '/volume1/主目录/Hermes/read/Projects/sfx-browser/dedup/fullhash.json'
print()
print('fullhash.json exists:', os.path.exists(fhp), (os.path.getsize(fhp) if os.path.exists(fhp) else ''))
if os.path.exists(fhp):
    with open(fhp, encoding='utf-8') as f:
        fh = json.load(f)
    t = type(fh).__name__
    print('type:', t, 'len:', len(fh))
    if isinstance(fh, dict):
        for k, v in list(fh.items())[:3]:
            print('  sample key:', repr(k)[:100])
            print('  sample val:', repr(v)[:160])
    else:
        print('  sample:', repr(fh[:3])[:300])
