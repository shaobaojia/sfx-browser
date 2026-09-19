#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""原始压缩包验收：逐个成员在 主库+隔离区 中查找并 CRC32 逐字节核验"""
import zipfile, os, zlib, csv, time
from collections import defaultdict, Counter

LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
Q   = "/volume1/主目录/Collection/素材&模板&音库/音效_去重待删_20260919"
Z   = os.path.join(LIB, "99_待整理/_原始压缩包")
ORG = "/volume1/主目录/Hermes/read/Projects/sfx-browser/organize"

def crc32f(p):
    c = 0
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b: break
            c = zlib.crc32(b, c)
    return c & 0xFFFFFFFF

t0 = time.time()
print("== 阶段1: 建索引（主库+隔离区）==", flush=True)
idx = defaultdict(list)
for base, tag in ((LIB, "lib"), (Q, "q")):
    n = 0
    for root, dirs, fns in os.walk(base):
        for fn in fns:
            p = os.path.join(root, fn)
            try: sz = os.path.getsize(p)
            except OSError: continue
            idx[fn.lower()].append((p, sz, tag))
            n += 1
    print("  %s: %d 文件  (%.0fs)" % (tag, n, time.time() - t0), flush=True)
print("  索引名条目: %d  (%.0fs)" % (len(idx), time.time() - t0), flush=True)

print("\n== 阶段2: 逐成员核验 ==", flush=True)
all_rows = []
for zn in sorted(os.listdir(Z)):
    if not zn.lower().endswith(".zip"): continue
    zp = os.path.join(Z, zn)
    z = zipfile.ZipFile(zp)
    files = [i for i in z.infolist() if not i.is_dir()]
    junk = [i for i in files if ("__MACOSX" in i.filename
            or i.filename.replace("\\", "/").split("/")[-1] in (".DS_Store", "Thumbs.db")
            or i.filename.replace("\\", "/").split("/")[-1].startswith("._"))]
    junkids = set(id(i) for i in junk)
    real = [i for i in files if id(i) not in junkids]
    stat = Counter()
    roots = Counter()
    examples = []
    for i in real:
        nm = i.filename.replace("\\", "/").split("/")[-1]
        msize = i.file_size
        mcrc = i.CRC & 0xFFFFFFFF
        cands = idx.get(nm.lower(), [])
        same_size = [c for c in cands if c[1] == msize]
        found = None; found_tag = None
        for (cp, csz, ctag) in same_size:
            try:
                if crc32f(cp) == mcrc:
                    found, found_tag = cp, ctag
                    break
            except OSError:
                continue
        if found:
            stat["ok_lib" if found_tag == "lib" else "ok_q"] += 1
            status = "OK" if found_tag == "lib" else "OK_Q"
            if len(examples) < 5:
                examples.append("      %s  ->  %s" % (i.filename, found))
            rel = os.path.relpath(found, LIB)
            roots["/".join(rel.split(os.sep)[:3])] += 1
        else:
            if cands:
                stat["name_only"] += 1
                status = "NAME_ONLY"
                found = cands[0][0]
            else:
                stat["missing"] += 1
                status = "MISSING"
                found = ""
        all_rows.append([zn, i.filename, msize, "%08x" % mcrc, status, found])

print("\n== 结果 ==")
for zn in sorted(set(r[0] for r in all_rows)):
    rows = [r for r in all_rows if r[0] == zn]
    total = len(rows)
    ok = sum(1 for r in rows if r[4] == "OK")
    okq = sum(1 for r in rows if r[4] == "OK_Q")
    no = sum(1 for r in rows if r[4] == "NAME_ONLY")
    mi = sum(1 for r in rows if r[4] == "MISSING")
    print("\n### %s" % zn)
    print("  成员总数 %d | 库内确认 %d | 仅隔离区 %d | 同名不同大小 %d | 完全缺失 %d"
          % (total, ok, okq, no, mi), flush=True)
    roots = Counter()
    for r in rows:
        if r[4] in ("OK", "OK_Q") and r[5]:
            roots["/".join(os.path.relpath(r[5], LIB).split(os.sep)[:3])] += 1
    print("  匹配落点 top:")
    for k, c in roots.most_common(8):
        print("     [%d] %s" % (c, k))
    ex = [r for r in rows if r[4] == "OK"][:4]
    print("  样例:")
    for r in ex:
        print("     %s  ->  %s" % (r[1], r[5]))
    iss = [r for r in rows if r[4] in ("NAME_ONLY", "MISSING")]
    if iss:
        print("  问题成员 (%d) 前40:" % len(iss))
        for r in iss[:40]:
            print("     [%s] %s (%d B) %s" % (r[4], r[1], r[2], r[5]))
        if len(iss) > 40: print("     ...")

with open(os.path.join(ORG, "zipaudit_members.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["zip", "member", "size", "crc32", "status", "matched_path"])
    w.writerows(all_rows)
print("\n已写 zipaudit_members.csv | 总耗时 %.0fs" % (time.time() - t0))
print("DONE")
