#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""去重后独立复检：1) 非音频撞车检查  2) 音频全库漏网复检（尺寸→指纹→全量md5）"""
import os, sqlite3, hashlib, json, time
from concurrent.futures import ThreadPoolExecutor
LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
BASE = "/volume1/主目录/Hermes/read/Projects/sfx-browser"
DED = os.path.join(BASE, "dedup")
DB = os.path.join(BASE, "data", "sfx.db")
t0 = time.time()

def md5f(p, size=None, quick=False):
    h = hashlib.md5()
    with open(p, "rb") as f:
        if quick and size is not None:
            h.update(f.read(65536))
            if size > 65536:
                f.seek(max(0, size - 65536)); h.update(f.read(65536))
            h.update(b"|%d" % size)
        else:
            while True:
                b = f.read(1 << 20)
                if not b: break
                h.update(b)
    return h.hexdigest()

con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
idx = set(r[0] for r in con.execute("SELECT rel FROM files"))
zero_idx = list(con.execute("SELECT COUNT(*) FROM files WHERE size=0"))[0][0]

# ---------- 1) 非音频 ----------
raw = []; zero_raw = 0
for root, dirs, files in os.walk(LIB):
    for fn in files:
        p = os.path.join(root, fn)
        try: st = os.stat(p)
        except OSError: continue
        raw.append((os.path.relpath(p, LIB), st.st_size))
        if st.st_size == 0: zero_raw += 1
non = [(rel, sz) for rel, sz in raw if rel not in idx]
print("1) 原始 %d | 音频(索引) %d | 非音频 %d | 0字节 %d(音频内 %d)" %
      (len(raw), len(idx), len(non), zero_raw, zero_idx), flush=True)
szg = {}
for rel, sz in non: szg.setdefault(sz, []).append(rel)
coll = {s: v for s, v in szg.items() if len(v) > 1 and s > 0}
n_files = sum(len(v) for v in coll.values())
up = sum((len(v) - 1) * s for s, v in coll.items())
print("   非音频尺寸撞车: %d 组 / %d 件 / 上界 %.1f MB" % (len(coll), n_files, up / 2**20), flush=True)
non_true = []
if 0 < n_files <= 8000:
    fg = {}
    for s, vs in coll.items():
        for rel in vs:
            try: hh = md5f(os.path.join(LIB, rel), s, quick=True)
            except OSError: continue
            fg.setdefault(hh, []).append((rel, s))
    mem = [x for k, v in fg.items() if len(v) > 1 for x in v]
    tg = {}
    for rel, s in mem:
        try: hh = md5f(os.path.join(LIB, rel))
        except OSError: continue
        tg.setdefault(hh, []).append((rel, s))
    non_true = [v for v in tg.values() if len(v) > 1]
    non_true.sort(key=lambda g: -(len(g) - 1) * g[0][1])
    nf = sum(len(g) - 1 for g in non_true); nb = sum((len(g) - 1) * g[0][1] for g in non_true)
    print("   非音频真重复: %d 组 / 冗余 %d 件 / %.2f MB" % (len(non_true), nf, nb / 2**20), flush=True)
    for g in non_true[:6]: print("     %d×%dB | %s" % (len(g), g[0][1], g[0][0][:72]))

# ---------- 2) 音频复检 ----------
sz2 = {}
for rel, size in con.execute("SELECT rel, size FROM files WHERE size>0"):
    sz2.setdefault(size, []).append(rel)
cand = []
for size, rels in sz2.items():
    if len(rels) > 1: cand += [(rel, size) for rel in rels]
cand.sort()
print("2) 音频复检·尺寸撞车候选: %d 件" % len(cand), flush=True)

def fpq(rs):
    rel, size = rs
    try: return (md5f(os.path.join(LIB, rel), size, quick=True), rel, size, None)
    except OSError as e: return (None, rel, size, str(e))
fg2 = {}; errs = []; done = 0
with ThreadPoolExecutor(max_workers=4) as ex:
    for hh, rel, size, err in ex.map(fpq, cand, chunksize=100):
        done += 1
        if err: errs.append(rel)
        else: fg2.setdefault(hh, []).append((rel, size))
        if done % 30000 == 0: print("   fp %d/%d" % (done, len(cand)), flush=True)
hcl = [v for k, v in fg2.items() if len(v) > 1]
hmembers = [x for g in hcl for x in g]
print("   指纹簇: %d 组 / %d 件 → 全量 md5..." % (len(hcl), len(hmembers)), flush=True)

def fullq(rs):
    rel, size = rs
    try: return (md5f(os.path.join(LIB, rel)), rel, size, None)
    except OSError as e: return (None, rel, size, str(e))
tg2 = {}; done = 0
with ThreadPoolExecutor(max_workers=4) as ex:
    for hh, rel, size, err in ex.map(fullq, hmembers, chunksize=50):
        done += 1
        if err: errs.append(rel)
        else: tg2.setdefault(hh, []).append({"rel": rel, "size": size})
        if done % 2000 == 0: print("   md5 %d/%d" % (done, len(hmembers)), flush=True)
true_c = [v for k, v in tg2.items() if len(v) > 1]
true_c.sort(key=lambda g: -(len(g) - 1) * g[0]["size"])
nf2 = sum(len(g) - 1 for g in true_c); nb2 = sum((len(g) - 1) * g[0]["size"] for g in true_c)
print("3) 音频漏网真重复: %d 组 / 冗余 %d 件 / %.2f MB" % (len(true_c), nf2, nb2 / 2**20), flush=True)
for g in true_c[:8]: print("     %d×%.1fMB | %s" % (len(g), g[0]["size"] / 2**20, g[0]["rel"][:70]))

summary = {"raw_files": len(raw), "audio_indexed": len(idx), "nonaudio": len(non),
           "nonaudio_coll_files": n_files, "nonaudio_coll_upper_bytes": up,
           "nonaudio_true_clusters": len(non_true),
           "nonaudio_true_excess": sum(len(g) - 1 for g in non_true),
           "audio_candidates": len(cand), "audio_fp_clusters": len(hcl),
           "audio_true_clusters": len(true_c), "audio_true_excess_files": nf2,
           "audio_true_excess_bytes": nb2, "errors": len(errs), "elapsed_s": round(time.time() - t0, 1)}
json.dump({"summary": summary, "audio_true_clusters": true_c,
           "nonaudio_true_clusters": [list(map(list, g)) for g in non_true]},
          open(os.path.join(DED, "recheck_20260919.json"), "w"), ensure_ascii=False)
print("RECHECK-DONE " + json.dumps(summary, ensure_ascii=False), flush=True)
