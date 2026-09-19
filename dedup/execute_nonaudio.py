#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""非音频冗余件移入隔离区（批次2）。--dry 演练。"""
import os, sys, json, csv, time
LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
QUAR = "/volume1/主目录/Collection/素材&模板&音库/音效_去重待删_20260919"
DED = "/volume1/主目录/Hermes/read/Projects/sfx-browser/dedup"
SRC = os.path.join(DED, "recheck_20260919.json")
OUT_CSV = os.path.join(DED, "moved.csv")

def score(rel):
    sc = rel.count("/") * 100 + len(rel)
    for bad in ("备用", "质量一般", "（1）", "(1)", "副本", "copy"):
        if bad in rel: sc += 2000
    segs = rel.split("/")
    for i in range(len(segs) - 1):
        if segs[i] and segs[i] == segs[i + 1]: sc += 800
    return sc

d = json.load(open(SRC, encoding="utf-8"))
cl = d["nonaudio_true_clusters"]
moves = []
seen = set()
for g in cl:
    mem = sorted((str(m[0]), int(m[1])) for m in g)
    keep = min(mem, key=lambda x: score(x[0]))
    for rel, sz in mem:
        if rel == keep[0]: continue
        assert rel not in seen, rel
        seen.add(rel)
        moves.append((rel, sz))
n = len(moves); total = sum(s for _, s in moves)
print("non-audio planned moves: %d files / %.2f GiB" % (n, total / 2**30), flush=True)

ext = {}
for rel, sz in moves:
    e = os.path.splitext(rel)[1].lower() or "(无扩展名)"
    a = ext.setdefault(e, [0, 0]); a[0] += 1; a[1] += sz
print("--- 按扩展名 TOP10 ---")
for e, (c2, s2) in sorted(ext.items(), key=lambda x: -x[1][1])[:10]:
    print("  %5d 件 / %8.1f MB ｜ %s" % (c2, s2 / 2**20, e))
print("--- TOP12 组（keep / rm） ---")
for g in cl[:12]:
    mem = sorted((str(m[0]), int(m[1])) for m in g)
    keep = min(mem, key=lambda x: score(x[0]))
    print("[%8.1f MB] %d份 ｜ keep: %s" % ((len(mem) - 1) * mem[0][1] / 2**20, len(mem), keep[0][:78]))
    for rel, sz in mem:
        if rel != keep[0]: print("             rm:   %s" % rel[:88])

if "--dry" in sys.argv:
    print("dry ok"); sys.exit(0)

t0 = time.time()
ok = errs = 0; moved_bytes = 0
f = open(OUT_CSV, "a", newline="", encoding="utf-8-sig")
wr = csv.writer(f)
if os.path.getsize(OUT_CSV) == 0: wr.writerow(["rel", "size_bytes"])
for rel, size in moves:
    src = os.path.join(LIB, rel); dst = os.path.join(QUAR, rel)
    if not os.path.exists(src) and os.path.exists(dst): ok += 1; continue
    if not os.path.exists(src): errs += 1; print("MISS:", rel[:80]); continue
    try:
        if os.path.getsize(src) != size: errs += 1; print("SIZE-CHANGED:", rel[:80]); continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        os.rename(src, dst); wr.writerow([rel, size]); ok += 1; moved_bytes += size
    except OSError as e:
        errs += 1; print("ERR:", rel[:80], e)
f.close()
pruned = 0
for root, dirs, files in os.walk(LIB, topdown=False):
    try:
        if not os.listdir(root): os.rmdir(root); pruned += 1
    except OSError: pass
print("NONAUDIO-DONE moved=%d bytes=%d errors=%d pruned_dirs=%d elapsed=%.1fs" %
      (ok, moved_bytes, errs, pruned, time.time() - t0), flush=True)
