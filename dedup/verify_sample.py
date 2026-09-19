#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抽样全量校验：TOP50 大簇 + 随机 250 簇，逐字节 md5 核对。"""
import os, json, hashlib, random, time
LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
DED = "/volume1/主目录/Hermes/read/Projects/sfx-browser/dedup"
d = json.load(open(os.path.join(DED, "scan_quick.json"), encoding="utf-8"))
cl = d["clusters"]
sample = cl[:50] + random.Random(20260919).sample(cl[50:], 250)
t0 = time.time(); bad = []; files = 0; nbytes = 0
for c in sample:
    hs = {}
    for m in c["members"]:
        try:
            h = hashlib.md5()
            with open(os.path.join(LIB, m), "rb") as f:
                while True:
                    b = f.read(1 << 20)
                    if not b: break
                    h.update(b)
            hs[m] = h.hexdigest(); files += 1; nbytes += c["size"]
        except OSError as e:
            hs[m] = "ERR:" + str(e)
    if len(set(hs.values())) != 1:
        bad.append({"members": hs})
print("clusters=%d files=%d bytes=%.2f GiB elapsed=%.0fs mismatches=%d" %
      (len(sample), files, nbytes / 2**30, time.time() - t0, len(bad)))
for b in bad[:8]: print("MISMATCH:", json.dumps(b, ensure_ascii=False)[:300])
if not bad: print("ALL-OK")
