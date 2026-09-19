#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""音效库查重 v1: 对"大小撞车"候选做(首64KB+尾64KB+大小)指纹，输出重复簇。"""
import os, sys, sqlite3, hashlib, json, time
from concurrent.futures import ThreadPoolExecutor

LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
BASE = "/volume1/主目录/Hermes/read/Projects/sfx-browser"
DB = os.path.join(BASE, "data", "sfx.db")
OUTDIR = os.path.join(BASE, "dedup")
os.makedirs(OUTDIR, exist_ok=True)
OUT = os.path.join(OUTDIR, "scan_quick.json")
PROG = os.path.join(OUTDIR, "scan_quick.progress")
SAMPLE = 65536

def log(*a): print(*a, flush=True)

def fingerprint(item):
    rel, size = item
    p = os.path.join(LIB, rel)
    h = hashlib.md5()
    try:
        with open(p, "rb") as f:
            h.update(f.read(SAMPLE))
            if size > SAMPLE:
                f.seek(max(0, size - SAMPLE))
                h.update(f.read(SAMPLE))
    except OSError as e:
        return (None, rel, size, str(e))
    h.update(b"|%d" % size)
    return (h.hexdigest(), rel, size, None)

def main():
    t0 = time.time()
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    cand_sizes = {r[0] for r in con.execute(
        "SELECT size FROM files WHERE size>0 GROUP BY size HAVING COUNT(*)>1")}
    rows = [(rel, size) for rel, size in con.execute("SELECT rel,size FROM files WHERE size>0")
            if size in cand_sizes]
    con.close()
    rows.sort()
    total = len(rows)
    log("candidates: %d" % total)

    groups, errs = {}, []
    done = 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        for hh, rel, size, err in ex.map(fingerprint, rows, chunksize=100):
            done += 1
            if err: errs.append({"rel": rel, "err": err})
            else: groups.setdefault(hh, []).append({"rel": rel, "size": size})
            if done % 5000 == 0:
                el = time.time() - t0
                rate = done / el
                eta = (total - done) / rate if rate > 0 else -1
                log("progress %d/%d  %.0f/s  eta %.0fmin" % (done, total, rate, eta / 60))
                with open(PROG, "w") as pf:
                    json.dump({"done": done, "total": total, "elapsed_s": round(el),
                               "eta_s": round(eta)}, pf)

    dups = []
    dup_files = 0
    dup_bytes = 0
    excess_bytes = 0
    for hh, members in groups.items():
        if len(members) > 1:
            members.sort(key=lambda m: m["rel"])
            sz = members[0]["size"]
            dirs = len({os.path.dirname(m["rel"]) for m in members})
            dups.append({"size": sz, "count": len(members), "dirs": dirs,
                         "waste": sz * (len(members) - 1),
                         "members": [m["rel"] for m in members]})
            dup_files += len(members)
            dup_bytes += sz * len(members)
            excess_bytes += sz * (len(members) - 1)
    dups.sort(key=lambda d: -d["waste"])
    summary = {"candidates": total, "clusters": len(dups), "dup_files": dup_files,
               "excess_files": dup_files - len(dups), "dup_bytes": dup_bytes,
               "excess_bytes": excess_bytes, "errors": len(errs),
               "elapsed_s": round(time.time() - t0, 1)}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "clusters": dups, "errors": errs}, f, ensure_ascii=False)
    log("SUMMARY " + json.dumps(summary, ensure_ascii=False))
    log("out -> %s" % OUT)

if __name__ == "__main__":
    main()
