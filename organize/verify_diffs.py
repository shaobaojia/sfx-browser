#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""50件NAME_ONLY的音频级对比 + OK_Q的全库异名副本搜索"""
import zipfile, os, subprocess, hashlib, csv, json, tempfile, shutil, zlib
from collections import defaultdict

LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
Q   = "/volume1/主目录/Collection/素材&模板&音库/音效_去重待删_20260919"
Z   = os.path.join(LIB, "99_待整理/_原始压缩包")
ORG = "/volume1/主目录/Hermes/read/Projects/sfx-browser/organize"
TMP = "/tmp/zipcheck"
if os.path.isdir(TMP): shutil.rmtree(TMP)
os.makedirs(TMP)

rows = []
with open(os.path.join(ORG, "zipaudit_members.csv"), encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r["status"] in ("NAME_ONLY", "OK_Q"):
            rows.append(r)

print("待处理: NAME_ONLY %d + OK_Q %d" % (
    sum(1 for r in rows if r["status"] == "NAME_ONLY"),
    sum(1 for r in rows if r["status"] == "OK_Q")), flush=True)

# 建 大小索引 + 名字索引（主库+隔离区）
by_size = defaultdict(list)
by_name = defaultdict(list)
for base, tag in ((LIB, "lib"), (Q, "q")):
    for root, dirs, fns in os.walk(base):
        for fn in fns:
            p = os.path.join(root, fn)
            try: sz = os.path.getsize(p)
            except OSError: continue
            by_size[sz].append((p, tag))
            by_name[fn.lower()].append((p, sz, tag))
print("索引就绪", flush=True)

def crc32f(p):
    c = 0
    with open(p, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b: break
            c = zlib.crc32(b, c)
    return c & 0xFFFFFFFF

def probe(path):
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
            "stream=sample_rate,channels,duration,bits_per_sample",
            "-of", "json", path], capture_output=True, timeout=120).stdout
        j = json.loads(out)
        st = j.get("streams", [{}])[0]
        return (st.get("sample_rate"), st.get("channels"),
                float(st.get("duration", 0) or 0), st.get("bits_per_sample"))
    except Exception as e:
        return ("ERR", str(e), 0, "")

def pcm_md5(path, ar="48000", ac="2"):
    try:
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "s16le",
                              "-ar", ar, "-ac", ac, "-"], stdout=subprocess.PIPE)
        h = hashlib.md5()
        while True:
            b = p.stdout.read(1 << 20)
            if not b: break
            h.update(b)
        p.wait()
        return h.hexdigest() if p.returncode == 0 else "FFMPEG_ERR_%d" % p.returncode
    except Exception as e:
        return "ERR:%s" % e

out_rows = []
print("\n== NAME_ONLY 音频级对比 ==", flush=True)
n = 0
for r in rows:
    if r["status"] != "NAME_ONLY": continue
    n += 1
    zn, member, msize = r["zip"], r["member"], int(r["size"])
    libp = r["matched_path"]
    z = zipfile.ZipFile(os.path.join(Z, zn))
    bn = os.path.basename(member.replace("\\", "/"))
    tmpf = os.path.join(TMP, "%03d_%s" % (n, bn))
    try:
        with z.open(member) as src, open(tmpf, "wb") as dst:
            shutil.copyfileobj(src, dst, 1 << 20)
    except Exception as e:
        print("  [%d] 抽取失败 %s: %s" % (n, member, e), flush=True)
        out_rows.append([zn, member, "EXTRACT_FAIL", str(e), "", "", ""])
        continue
    zsz = os.path.getsize(tmpf)
    zpr = probe(tmpf); lpr = probe(libp)
    zm = pcm_md5(tmpf); lm = pcm_md5(libp)
    same = (zm == lm and not zm.startswith("ERR") and not zm.startswith("FFMPEG"))
    # 时长比
    durz, durl = zpr[2], lpr[2]
    rat = (durz / durl) if durl else 0
    verdict = "PCM一致" if same else ("时长差%.1f%%" % (abs(rat - 1) * 100) if durl else "?")
    print("  [%d] %s" % (n, bn), flush=True)
    print("      zip: %s Hz/%sch/%.1fs/%d B  |  lib: %s Hz/%sch/%.1fs/%d B  => %s"
          % (zpr[0], zpr[1], durz, zsz, lpr[0], lpr[1], durl, os.path.getsize(libp), verdict), flush=True)
    out_rows.append([zn, member, "PCM一致" if same else "PCM不同",
                     "zip %s/%s/%ss" % (zpr[0], zpr[1], round(durz, 2)),
                     "lib %s/%s/%ss" % (lpr[0], lpr[1], round(durl, 2)),
                     zm, lm])

print("\n== OK_Q 全库异名副本搜索 ==", flush=True)
for r in rows:
    if r["status"] != "OK_Q": continue
    zn, member, msize = r["zip"], r["member"], int(r["size"])
    qpath = r["matched_path"]
    qcrc = crc32f(qpath)
    found = []
    for (p, tag) in by_size.get(msize, []):
        if p == qpath: continue
        try:
            if crc32f(p) == qcrc:
                found.append(p); 
        except OSError: continue
    lib_hits = [p for p in found if p.startswith(LIB)]
    print("  %s" % os.path.basename(qpath), flush=True)
    print("      大小 %d B | 库内异名同内容副本: %s" % (msize, ("%d 个 -> %s" % (len(lib_hits), lib_hits[0])) if lib_hits else "无（仅隔离区有）"), flush=True)
    out_rows.append([zn, member, "OK_Q检查", "库内异名副本 %d" % len(lib_hits), "", "", ""])

with open(os.path.join(ORG, "verify_diffs.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["zip", "member", "结论", "zip参数", "lib参数", "pcm_zip", "pcm_lib"])
    w.writerows(out_rows)
print("\n已写 verify_diffs.csv")
print("DONE")
