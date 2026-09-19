#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""音效库去重·执行：把重复簇的冗余件移入隔离区（可回滚；--dry 只演练）。"""
import os, sys, json, csv, time
LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
QUAR = "/volume1/主目录/Collection/素材&模板&音库/音效_去重待删_20260919"
BASE = "/volume1/主目录/Hermes/read/Projects/sfx-browser"
DED = os.path.join(BASE, "dedup")
SRC = os.path.join(DED, "fullhash.json")
OUT_CSV = os.path.join(DED, "moved.csv")
OUT_REP = os.path.join(DED, "execution_report.json")
PROG = os.path.join(DED, "execute.progress")

def score(rel):
    sc = rel.count("/") * 100 + len(rel)
    for bad in ("备用", "质量一般", "（1）", "(1)", "副本", "copy"):
        if bad in rel: sc += 2000
    segs = rel.split("/")
    for i in range(len(segs) - 1):
        if segs[i] and segs[i] == segs[i + 1]: sc += 800
    return sc

def main():
    dry = "--dry" in sys.argv
    t0 = time.time()
    d = json.load(open(SRC, encoding="utf-8"))
    cl = d["clusters"]
    assert sum(len(c["members"]) for c in cl) == sum(c["count"] for c in cl)
    print("LIB dev:", os.stat(LIB).st_dev, "| QUAR-parent dev:", os.stat(os.path.dirname(QUAR)).st_dev, flush=True)
    moves = []
    seen = set()
    for c in cl:
        keep = min(c["members"], key=score)
        for m in c["members"]:
            assert m not in seen, "member in multiple clusters!"
            seen.add(m)
            if m != keep:
                moves.append((m, c["size"]))
    n = len(moves)
    total_bytes = sum(s for _, s in moves)
    print("planned moves: %d files / %.1f GiB" % (n, total_bytes / 2**30), flush=True)
    if dry:
        segs = {}
        for rel, sz in moves:
            seg = rel.split("/", 1)[0] if "/" in rel else "(根级)"
            a = segs.setdefault(seg, [0, 0]); a[0] += 1; a[1] += sz
        print("--- 迁出量按顶层段 TOP12 ---")
        for seg, (cnt, sz) in sorted(segs.items(), key=lambda x: -x[1][1])[:12]:
            print("  %6d 个 / %8.1f GiB ｜ %s" % (cnt, sz / 2**30, seg[:60]))
        print("--- TOP12 簇（keep=保留 / rm=移走） ---")
        for c in cl[:12]:
            keep = min(c["members"], key=score)
            print("[%7.0f MiB] %d份 ｜ keep: %s" % (c["waste"] / 2**20, c["count"], keep[:80]))
            for m in c["members"]:
                if m != keep:
                    print("            rm:   %s" % m[:90])
        print("dry done in %.1fs" % (time.time() - t0))
        return
    os.makedirs(QUAR, exist_ok=True)
    f = open(OUT_CSV, "a", newline="", encoding="utf-8-sig")
    wr = csv.writer(f)
    if os.path.getsize(OUT_CSV) == 0: wr.writerow(["rel", "size_bytes"])
    done = 0; ok = 0; errs = []; moved_bytes = 0
    f.flush()
    for i, (rel, size) in enumerate(moves):
        src = os.path.join(LIB, rel); dst = os.path.join(QUAR, rel)
        if not os.path.exists(src) and os.path.exists(dst): ok += 1; done += 1; continue
        if not os.path.exists(src): errs.append((rel, "source missing")); done += 1; continue
        try:
            if os.path.getsize(src) != size: errs.append((rel, "size-changed")); done += 1; continue
        except OSError:
            errs.append((rel, "stat failed")); done += 1; continue
        if os.path.exists(dst): errs.append((rel, "dest exists")); done += 1; continue
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            os.rename(src, dst)
            wr.writerow([rel, size]); ok += 1; moved_bytes += size
        except OSError as e:
            errs.append((rel, str(e)))
        done += 1
        if done % 10000 == 0:
            f.flush()
            el = time.time() - t0
            eta = (n - done) * (el / max(done, 1))
            print("progress %d/%d  ok=%d err=%d  eta %.1fmin" % (done, n, ok, len(errs), eta / 60), flush=True)
            json.dump({"done": done, "total": n, "ok": ok, "err": len(errs)}, open(PROG, "w"))
    f.close()
    pruned = 0
    for root, dirs, files in os.walk(LIB, topdown=False):
        try:
            if not os.listdir(root): os.rmdir(root); pruned += 1
        except OSError: pass
    rep = {"moved": ok, "bytes_moved": moved_bytes, "errors": len(errs),
           "error_samples": errs[:30], "empty_dirs_pruned": pruned,
           "elapsed_s": round(time.time() - t0, 1)}
    json.dump(rep, open(OUT_REP, "w"), ensure_ascii=False, indent=1)
    print("DONE " + json.dumps({"moved": ok, "GiB": round(moved_bytes / 2**30, 1),
          "errors": len(errs), "pruned_dirs": pruned, "elapsed_s": rep["elapsed_s"]}, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    main()
