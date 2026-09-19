#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量 md5 复核：逐字节哈希全部重复簇成员，重算真实重复组（权威口径）。"""
import os, json, hashlib, time, csv
from concurrent.futures import ThreadPoolExecutor
LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
DED = "/volume1/主目录/Hermes/read/Projects/sfx-browser/dedup"
d = json.load(open(os.path.join(DED, "scan_quick.json"), encoding="utf-8"))
members = []
for c in d["clusters"]:
    for m in c["members"]:
        members.append((m, c["size"]))
members.sort()
total = len(members)
print("members to hash: %d" % total, flush=True)
t0 = time.time()

def full(rs):
    rel, size = rs
    h = hashlib.md5()
    try:
        with open(os.path.join(LIB, rel), "rb") as f:
            while True:
                b = f.read(1 << 20)
                if not b: break
                h.update(b)
    except OSError as e:
        return (None, rel, size, str(e))
    return (h.hexdigest(), rel, size, None)

groups = {}
errors = []
done = 0
csvf = open(os.path.join(DED, "full_md5.csv"), "w", newline="", encoding="utf-8-sig")
wr = csv.writer(csvf)
wr.writerow(["rel", "size", "md5"])
with ThreadPoolExecutor(max_workers=4) as ex:
    for md5, rel, size, err in ex.map(full, members, chunksize=40):
        done += 1
        if err:
            errors.append({"rel": rel, "err": err})
        else:
            groups.setdefault(md5, []).append({"rel": rel, "size": size})
            wr.writerow([rel, size, md5])
        if done % 5000 == 0:
            csvf.flush()
            el = time.time() - t0
            eta = (total - done) * (el / done)
            print("progress %d/%d  %.0f/s  eta %.1fmin" % (done, total, done / el, eta / 60), flush=True)
csvf.close()
true_clusters = []
for md5, mem in groups.items():
    if len(mem) > 1:
        mem.sort(key=lambda x: x["rel"])
        sz = mem[0]["size"]
        true_clusters.append({"md5": md5, "size": sz, "count": len(mem),
                              "waste": sz * (len(mem) - 1),
                              "dirs": len({m["rel"].rsplit("/", 1)[0] if "/" in m["rel"] else "" for m in mem}),
                              "members": [m["rel"] for m in mem]})
true_clusters.sort(key=lambda c: -c["waste"])
exf = sum(c["count"] - 1 for c in true_clusters)
exb = sum(c["waste"] for c in true_clusters)
summary = {"members_hashed": total, "true_clusters": len(true_clusters),
           "true_excess_files": exf, "true_excess_bytes": exb,
           "singles": total - sum(c["count"] for c in true_clusters),
           "errors": len(errors), "elapsed_s": round(time.time() - t0, 1)}
json.dump({"summary": summary, "clusters": true_clusters, "errors": errors[:200]},
          open(os.path.join(DED, "fullhash.json"), "w"), ensure_ascii=False)
print("ALLDONE " + json.dumps(summary, ensure_ascii=False), flush=True)
