#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vol.2 音频CD镜像 → 99 轨 wav（按 cue 分轨 + pdf 命名 + 字节核验 + sha256 留档后删 bin）"""
import os, re, struct, hashlib, subprocess, sys, array

V2  = "/volume1/主目录/Collection/素材&模板&音库/音效/01_商业音效包/[Sound.Ideas]The Metropolis Science Fiction Toolkit Vol.2"
BIN = os.path.join(V2, "dyn-simsftkv2.bin")
CUE = os.path.join(V2, "dyn-simsftkv2.cue")
PDF = os.path.join(V2, "metro2.pdf")
ORG = "/volume1/主目录/Hermes/read/Projects/sfx-browser/organize"
LOG = os.path.join(ORG, "vol2_convert_20260919.log")

fsize = os.path.getsize(BIN)
print("bin 大小: %d" % fsize)

# 1) 解析 cue
t = open(CUE, encoding="latin-1").read().replace("\r", " ").replace("\n", " ")
offs = []
for m in re.finditer(r"TRACK\s+(\d+)\s+AUDIO\s+INDEX\s+01\s+(\d+):(\d+):(\d+)", t):
    tr = int(m.group(1)); mm, ss, ff = int(m.group(2)), int(m.group(3)), int(m.group(4))
    offs.append((tr, ((mm * 60 + ss) * 75 + ff) * 2352))
offs.sort()
trax = [o[0] for o in offs]; starts = [o[1] for o in offs]
assert len(trax) == 99, "轨数 %d != 99" % len(trax)
assert starts[0] == 0 and all(starts[i] < starts[i + 1] for i in range(len(starts) - 1)), "偏移异常"
assert starts[-1] < fsize, "最后一轨起点越界"
print("cue 轨数: %d, 最后一轨起点: %d" % (len(trax), starts[-1]))

# 2) 解析 pdf 命名
pt = subprocess.run(["pdftotext", "-layout", PDF, "-"], capture_output=True, text=True).stdout
names = {}
for m in re.finditer(r"MET02\s+(\d+)-(\d+)\s+(.+?)\s+:\d+", pt):
    tr = int(m.group(1)); d = m.group(3).strip()
    names.setdefault(tr, []).append(d)

def safe(d):
    s = d.lower().replace("/", "-").replace("\\", "-")
    s = re.sub(r"\s+", " ", s).strip(" -")
    return s

# 3) 分轨转换
total_pcm = 0
lines = []
first_wav = None
with open(BIN, "rb") as f:
    for i, tr in enumerate(trax):
        start = starts[i]
        end = starts[i + 1] if i + 1 < len(starts) else fsize
        nb = end - start
        assert nb % 4 == 0
        f.seek(start)
        data = f.read(nb)
        a = array.array("h"); a.frombytes(data); a.byteswap()
        d = names.get(tr, [])
        nm = safe(d[0]) if d else ("track %02d" % tr)
        fn = "%02d. %s.wav" % (tr, nm)
        p = os.path.join(V2, fn); k = 2
        while os.path.exists(p):
            fn = "%02d. %s_%d.wav" % (tr, nm, k); p = os.path.join(V2, fn); k += 1
        with open(p, "wb") as w:
            w.write(b"RIFF" + struct.pack("<I", 36 + len(a) * 2) + b"WAVE")
            w.write(b"fmt " + struct.pack("<IHHIIHH", 16, 1, 2, 44100, 176400, 4, 16))
            w.write(b"data" + struct.pack("<I", len(a) * 2) + a.tobytes())
        total_pcm += len(a) * 2
        if first_wav is None: first_wav = p
        if i < 5 or i >= len(trax) - 5:
            lines.append("  %s | %.1f 秒" % (fn, len(a) / 2 / 44100))
        elif i == 5:
            lines.append("  ...(中间省略)...")

print("生成 %d 个 wav | PCM 总字节 %d (bin %d)" % (len(trax), total_pcm, fsize))
if total_pcm != fsize:
    print("!! PCM 总量与 bin 不一致，中止（不删 bin）"); sys.exit(1)
print("字节级核验通过 ✓")
r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                    "stream=sample_rate,channels,duration", "-of", "csv", first_wav],
                   capture_output=True, text=True)
print("首轨探测: %s" % r.stdout.strip())

# 4) sha256 留档 → 删 bin
h = hashlib.sha256()
with open(BIN, "rb") as f:
    while True:
        b = f.read(1 << 22)
        if not b: break
        h.update(b)
with open(LOG, "w", encoding="utf-8") as f:
    f.write("Vol.2 转换记录 2026-09-19\n")
    f.write("bin: %d B | sha256=%s\n" % (fsize, h.hexdigest()))
    f.write("wav 数: %d | PCM 总字节: %d（与 bin 一致）\n" % (len(trax), total_pcm))
    f.write("\n".join(lines) + "\n")
os.remove(BIN)
print("bin sha256=%s" % h.hexdigest())
print("bin 已删除；cue 与手册 pdf 保留")
print("DONE")
