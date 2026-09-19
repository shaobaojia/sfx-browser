#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""音效库结构侦察：顶层构成 / 同名目录分布 / 套娃 / 备用区 / 垃圾命名 / 深度"""
import os, collections, re
LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
REPO = "/volume1/主目录/Hermes/read/Projects/sfx-browser"
OUT = os.path.join(REPO, "organize", "recon_20260919.txt")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
L = []
def p(s=""):
    print(s, flush=True); L.append(s)

files = []
for root, dirs, fns in os.walk(LIB):
    for fn in fns:
        fpth = os.path.join(root, fn)
        try: st = os.stat(fpth)
        except OSError: continue
        files.append((os.path.relpath(fpth, LIB), st.st_size))
p("总文件: %d" % len(files))

dirfiles = collections.defaultdict(lambda: [0, 0])
for rel, sz in files:
    d = os.path.dirname(rel)
    dirfiles[d][0] += 1; dirfiles[d][1] += sz

# 1) 顶层构成
top = collections.defaultdict(lambda: [0, 0])
for rel, sz in files:
    seg = rel.split("/", 1)[0] if "/" in rel else "(根级文件)"
    top[seg][0] += 1; top[seg][1] += sz
p()
p("== 顶层构成（%d 项）==" % len(top))
for seg, (c, s) in sorted(top.items(), key=lambda x: -x[1][1]):
    p("  %6d 个 / %9.2f GiB ｜ %s" % (c, s / 2**30, seg[:70]))

# 2) 音效/ 第二层
lv2 = collections.defaultdict(lambda: [0, 0])
for rel, sz in files:
    parts = rel.split("/")
    if parts[0] == "音效" and len(parts) > 1:
        lv2["音效/" + parts[1]][0] += 1
        lv2["音效/" + parts[1]][1] += sz
p()
p("== 音效/ 第二层（%d 项）==" % len(lv2))
for seg, (c, s) in sorted(lv2.items(), key=lambda x: -x[1][1])[:50]:
    p("  %6d 个 / %9.2f GiB ｜ %s" % (c, s / 2**30, seg[:70]))

# 3) 同名文件夹分布
byname = collections.defaultdict(lambda: [])
for d, (c, s) in dirfiles.items():
    if d == "": continue
    byname[d.split("/")[-1].strip().lower()].append((d, c, s))
multi = []
for n, lst in byname.items():
    tot = sum(x[2] for x in lst)
    if len(lst) >= 2 and tot > 100 * 2**20:
        multi.append((n, lst, tot))
p()
p("== 同名文件夹（≥2处 & >100MiB）TOP25 ==")
for n, lst, tot in sorted(multi, key=lambda x: -x[2])[:25]:
    p("  [%6.2f GiB / %d处] %s" % (tot / 2**30, len(lst), n[:50]))
    for d, c, s in sorted(lst, key=lambda x: -x[2])[:4]:
        p("       %6d个 %7.2fGiB ← %s" % (c, s / 2**30, d[:80]))

# 4) 套娃
nest = set()
for d in dirfiles:
    segs = d.split("/")
    for i in range(len(segs) - 1):
        if segs[i] and segs[i] == segs[i + 1]:
            nest.add(d); break
nf = sum(dirfiles[d][0] for d in nest)
p()
p("== 连续同名套娃目录: %d 个 / 内含文件 %d ==" % (len(nest), nf))
for d in sorted(nest, key=lambda d: -dirfiles[d][0])[:12]:
    p("   %6d个 ｜ %s" % (dirfiles[d][0], d[:95]))

# 5) 备用/meta 区
for kw in ("备用", "质量一般"):
    hit = [(d, dirfiles[d]) for d in dirfiles if kw in d]
    p()
    p("== 含「%s」目录: %d 个 / 文件 %d / %.2f GiB ==" % (kw, len(hit), sum(c for _, (c, s) in hit), sum(s for _, (c, s) in hit) / 2**30))
    for d, (c, s) in sorted(hit, key=lambda x: -x[1][1])[:8]:
        p("   %6d个 %7.2fGiB ｜ %s" % (c, s / 2**30, d[:90]))

# 6) 垃圾命名目录
pat_id = re.compile(r"\d{9,}")
jd = []
for d, (c, s) in dirfiles.items():
    if d == "": continue
    base = d.split("/")[-1]
    if ("【" in base and "】" in base) or pat_id.search(base) or any(k in base for k in ("百度", "分享", "加群", "下载")):
        jd.append((d, c, s))
p()
p("== 疑似下载垃圾命名目录: %d 个 ==" % len(jd))
for d, c, s in sorted(jd, key=lambda x: -x[2])[:20]:
    p("   %6d个 %7.2fGiB ｜ %s" % (c, s / 2**30, d[:95]))

# 7) 包定位（归位目标素材）
p()
p("== 关键包散落分布 ==")
for k in ("Blastwave", "Bluezone", "Boom", "Sound.Ideas", "Sound Morph", "Pro Sound", "Wind", "Multiply",
          "Sample", "LTT", "布斯", "气氛", "电影级", "魔法", "预告", "音效素材", "BD音效库", "极品", "临时"):
    hits = [(d, dirfiles[d]) for d in dirfiles if k.lower() in d.lower() and dirfiles[d][0] > 0]
    hits.sort(key=lambda x: -x[1][1])
    tot = sum(s for _, (c, s) in hits)
    top3 = "; ".join("%s(%d)" % (d[:55], c) for d, (c, s) in hits[:3])
    p("  %-12s: %2d处 %7.1fGiB ｜ %s" % (k, len(hits), tot / 2**30, top3[:130]))

# 8) 深度
depth = collections.Counter()
for rel, _ in files:
    depth[rel.count("/")] += 1
p()
p("== 文件所在深度分布(含文件名层): %s" % sorted(depth.items()))
p("根级散文件: %d ｜ 音效/ 根级: %d" % (dirfiles.get("", [0])[0], dirfiles.get("音效", [0])[0]))

open(OUT, "w", encoding="utf-8").write("\n".join(L))
p()
p("saved -> %s" % OUT)
