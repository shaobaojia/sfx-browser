#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Lens Distortions 归一：气氛音乐音效(5产品) + 大气深沉1-6残部 → 01_商业音效包/Lens Distortions/
# 用法: python3 ld_merge.py --dry   |   --execute
import sys, os, glob, csv, hashlib

AMP = chr(38)
BASE = [x for x in glob.glob('/volume1/*/Collection/*/') if AMP in x][0].rstrip('/')
LIB = BASE + '/音效'
P02 = LIB + '/02_中文音效合集'
ORG = '/volume1/主目录/Hermes/read/Projects/sfx-browser/organize'
TARGET = LIB + '/01_商业音效包/Lens Distortions'
JUNK = LIB + '/99_待整理/_小杂件_LD_20260919'
LOG = ORG + '/ld_move_log.csv'

M = [
 {'en': 'Anticipation SFX',
  'dst': 'Anticipation SFX（大气深沉1 · 大气转场撞击重低音气氛无损音效素材包）',
  'main': P02 + '/气氛音乐音效/Anticipation SFX',
  'rem': [P02 + '/大气深沉1【音效：大气转场撞击重低音气氛无损音效素材包】/Anticipation_SFX',
          P02 + '/气氛音乐音效/Archetype SFX/01 - Risers/Risers - Silk/Anticipation SFX - MP3'],
  'strip': ['Anticipation SFX - MP3']},
 {'en': 'Archetype SFX',
  'dst': 'Archetype SFX（大气深沉2 · 紧张气氛片头转场渲染无损音效素材包）',
  'main': P02 + '/气氛音乐音效/Archetype SFX',
  'exclude': ['01 - Risers/Risers - Silk/Anticipation SFX - MP3'],
  'rem': [P02 + '/大气深沉2【音效：紧张气氛片头转场渲染无损音效素材包】/Archetype_SFX'],
  'strip': ['Archetype SFX MP3', 'Archetype SFX WAV']},
 {'en': 'Endurance SFX',
  'dst': 'Endurance SFX（大气深沉3 · 低音节奏感紧张气氛渲染无损音效素材包）',
  'main': P02 + '/气氛音乐音效/Endurance SFX',
  'rem': [P02 + '/大气深沉3【音效：低音节奏感紧张气氛渲染无损音效素材包】/Endurance_SFX'],
  'strip': ['Endurance SFX - MP3', 'Endurance SFX - WAV']},
 {'en': 'Idyllic SFX',
  'dst': 'Idyllic SFX（大气深沉4 · 优雅舒缓大气深沉叙事纪录婚礼电影广告环境配乐背景音乐）',
  'main': P02 + '/气氛音乐音效/Idyllic',
  'rem': [P02 + '/大气深沉4【优雅舒缓大气深沉叙事纪录婚礼电影广告环境配乐背景音乐】/Idyllic SFX'],
  'strip': ['MP3']},
 {'en': 'Statement SFX',
  'dst': 'Statement SFX（大气深沉5 · 大气深沉浑厚有力重低音环境气氛微电影抖音渲染音效）',
  'main': P02 + '/气氛音乐音效/Statement SFX',
  'rem': [P02 + '/大气深沉5【音效：大气深沉浑厚有力重低音环境气氛微电影抖音渲染音效】/Statement环境气氛WAV音效'],
  'strip': []},
 {'en': 'Beginnings SFX',
  'dst': 'Beginnings SFX（大气深沉6 · 大气深沉剧情叙事环境气氛渲染配乐背景音乐）',
  'main': None,
  'rem': [P02 + '/大气深沉6【大气深沉剧情叙事环境气氛渲染配乐背景音乐】/LD - Beginnings'],
  'strip': ['Beginnings - MP3', 'Beginnings - WAV']},
]

JUNK_NAMES = {'_ds_store', 'thumbs.db'}
JUNK_EXTS = {'.url'}


def strip_rel(rel, strip):
    parts = rel.split('/')
    while parts and parts[0] in strip:
        parts = parts[1:]
    return '/'.join(parts)


def md5(fp):
    h = hashlib.md5()
    with open(fp, 'rb') as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def collect():
    moves = []   # (src_abs, dst_rel, group_label)
    junk = []
    for m in M:
        excl = m.get('exclude', [])
        srcs = [('main', m['main'], [])] + [('rem', r, m['strip']) for r in m['rem']]
        for tag, src_abs, strip in srcs:
            if not src_abs:
                continue
            if not os.path.isdir(src_abs):
                print('!! 源目录缺失: %s' % src_abs)
                continue
            label = '%s/%s' % (m['en'], tag)
            for r, dd, fs in os.walk(src_abs):
                for f in fs:
                    fp = os.path.join(r, f)
                    rel0 = os.path.relpath(fp, src_abs)
                    if any(rel0 == e or rel0.startswith(e + '/') for e in excl):
                        continue
                    rel = strip_rel(rel0, strip)
                    low = f.lower()
                    if low in JUNK_NAMES or os.path.splitext(low)[1] in JUNK_EXTS:
                        junk.append((fp, '%s/%s' % (m['en'], rel), label))
                    else:
                        moves.append((fp, m['dst'] + '/' + rel, label))
    return moves, junk


def plan(moves):
    used = {}       # dst_rel -> src_abs
    final = []      # (src_abs, dst_rel, note)
    conflicts = []
    dupskip = []
    for src, dst, label in moves:
        if dst not in used:
            used[dst] = src
            final.append((src, dst, ''))
            continue
        prev = used[dst]
        if os.path.getsize(prev) == os.path.getsize(src) and md5(prev) == md5(src):
            dupskip.append((src, dst))
            continue
        stem, ext = os.path.splitext(dst)
        i = 2
        while True:
            cand = '%s_%d%s' % (stem, i, ext)
            if cand not in used:
                break
            i += 1
        used[cand] = src
        final.append((src, cand, 'conflict->suffix_%d' % i))
        conflicts.append((dst, prev, src))
    return final, conflicts, dupskip


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else '--dry'
    moves, junk = collect()
    final, conflicts, dupskip = plan(moves)
    per = {}
    for src, dst, note in final:
        prod = dst.split('/')[0]
        per[prod] = per.get(prod, 0) + 1
    print('=== 计划汇总 ===')
    for m in M:
        c = per.get(m['dst'], 0)
        print('  %-24s → %s : %d 件' % (m['en'], m['dst'], c))
    print('合计搬入: %d 件；重名冲突转后缀: %d；字节相同跳过: %d；杂件: %d' %
          (len(final), len(conflicts), len(dupskip), len(junk)))
    print('杂件明细:')
    for fp, jrel, label in junk:
        print('   ', jrel)
    if conflicts:
        print('冲突样例(前20):')
        for dst, prev, src in conflicts[:20]:
            print('   %s\n      A:%s\n      B:%s' % (dst, prev[-90:], src[-90:]))

    if mode == '--dry':
        print('DRY-OK（未动文件）')
        return

    if os.path.exists(TARGET):
        print('!! 目标已存在，拒绝执行'); return
    os.makedirs(TARGET, exist_ok=True)
    logf = open(LOG, 'w', encoding='utf-8')
    logf.write('src\tdst\tnote\n')
    n = 0
    fails = 0
    for src, dst, note in final:
        to = os.path.join(TARGET, dst)
        try:
            os.makedirs(os.path.dirname(to), exist_ok=True)
            os.rename(src, to)
            logf.write('%s\t%s\t%s\n' % (src, dst, note))
            n += 1
        except OSError as e:
            fails += 1
            logf.write('%s\t%s\tFAIL:%s\n' % (src, dst, e))
            print('FAIL:', src, '->', dst, e)
    for fp, jrel, label in junk:
        to = os.path.join(JUNK, jrel)
        try:
            os.makedirs(os.path.dirname(to), exist_ok=True)
            os.rename(fp, to)
            logf.write('%s\t%s\tjunk\n' % (fp, 'JUNK/' + jrel))
        except OSError as e:
            fails += 1
            print('JUNK-FAIL:', fp, e)
    logf.close()
    print('已搬入 %d 件；杂件 %d 件 → %s；失败 %d' % (n, len(junk), JUNK, fails))

    # 清空目录
    pr = 0
    roots = [P02 + '/气氛音乐音效'] + [P02 + '/' + d for d in sorted(os.listdir(P02)) if d.startswith('大气深沉')]
    for root in roots:
        if not os.path.isdir(root):
            continue
        for r, dd, fs in os.walk(root, topdown=False):
            for d in dd:
                dp = os.path.join(r, d)
                try:
                    if not os.listdir(dp):
                        os.rmdir(dp); pr += 1
                except OSError:
                    pass
        if not os.listdir(root):
            os.rmdir(root)
            print('已移除空目录:', root.split('/')[-1][:40])
        else:
            rest = sum(len(fs) for _, _, fs in os.walk(root))
            print('!! 未清空:', root, rest)
    print('清理空目录 %d 个' % pr)
    print('EXEC-DONE')


if __name__ == '__main__':
    main()
