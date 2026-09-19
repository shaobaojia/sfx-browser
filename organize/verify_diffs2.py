#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""50件NAME_ONLY的终极复核：WAV块结构对比 + 原生采样率32bit逐样本md5"""
import zipfile, os, subprocess, hashlib, csv, struct, shutil

LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
Z   = os.path.join(LIB, "99_待整理/_原始压缩包")
ORG = "/volume1/主目录/Hermes/read/Projects/sfx-browser/organize"
TMP = "/tmp/zipcheck"

def chunks(f):
    out = []
    fsz = os.path.getsize(f)
    with open(f, "rb") as fh:
        head = fh.read(12)
        if head[:4] != b"RIFF":
            return [("NON-RIFF", fsz)]
        pos = 12
        while pos + 8 <= fsz:
            fh.seek(pos)
            ch = fh.read(8)
            if len(ch) < 8: break
            cid = ch[:4].decode("ascii", "replace")
            sz = struct.unpack("<I", ch[4:8])[0]
            out.append((cid, sz))
            pos += 8 + sz + (sz & 1)
    return out

def md5native(path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "s32le", "-"],
                         stdout=subprocess.PIPE)
    h = hashlib.md5()
    while True:
        b = p.stdout.read(1 << 20)
        if not b: break
        h.update(b)
    p.wait()
    return h.hexdigest() if p.returncode == 0 else "FFMPEG_ERR"

paths = {}
with open(os.path.join(ORG, "zipaudit_members.csv"), encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r["status"] == "NAME_ONLY":
            paths[(r["zip"], r["member"])] = r["matched_path"]

rows = []
with open(os.path.join(ORG, "verify_diffs.csv"), encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r["结论"] == "PCM一致":
            r["matched_path"] = paths.get((r["zip"], r["member"]), "")
            rows.append(r)
print("复核 %d 件" % len(rows), flush=True)

n = 0; ok_data = 0; ok_md5 = 0; issues = []
for r in rows:
    n += 1
    member = r["member"]; libp = r["matched_path"]
    bn = os.path.basename(member.replace("\\", "/"))
    tmpf = os.path.join(TMP, "%03d_%s" % (n, bn))
    if not os.path.exists(tmpf):
        os.makedirs(TMP, exist_ok=True)
        z = zipfile.ZipFile(os.path.join(Z, r["zip"]))
        with z.open(member) as src, open(tmpf, "wb") as dst:
            shutil.copyfileobj(src, dst, 1 << 20)
    cz = dict(chunks(tmpf)); cl = dict(chunks(libp))
    dz = cz.get("data"); dl = cl.get("data")
    same_data = (dz == dl and dz is not None)
    if same_data: ok_data += 1
    mz = md5native(tmpf); ml = md5native(libp)
    same_md5 = (mz == ml and not mz.startswith("FFMPEG"))
    if same_md5: ok_md5 += 1
    if not (same_data and same_md5):
        issues.append((bn, dz, dl, same_md5))
    ekz = [c for c in cz if c not in ("fmt ", "data")]
    ekl = [c for c in cl if c not in ("fmt ", "data")]
    flag = "OK" if (same_data and same_md5) else "!!"
    print("  [%02d] %s %s" % (n, flag, bn), flush=True)
    if not (same_data and same_md5):
        print("        data块: zip %s vs lib %s | 原生md5同: %s" % (dz, dl, same_md5), flush=True)

print("\n汇总: data块同尺寸 %d/%d | 原生32bit逐样本一致 %d/%d" % (ok_data, len(rows), ok_md5, len(rows)))
if issues:
    print("!! 需关注 %d 件:" % len(issues))
    for b, dz, dl, sm in issues:
        print("   %s | data: %s vs %s | md5同:%s" % (b, dz, dl, sm))
else:
    print("全部通过：50/50 音频数据逐样本一致（原生采样率、32bit 精度）")
print("DONE")
