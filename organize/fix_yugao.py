#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""预告修正：Sinematic→01、Visual Tone rar 解压核验后删、收壳、映射表维护段"""
import os, subprocess, hashlib, datetime, sys

LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
ORG = "/volume1/主目录/Hermes/read/Projects/sfx-browser/organize"
YG  = os.path.join(LIB, "03_项目素材/预告")
B1  = os.path.join(LIB, "01_商业音效包")
RAR = os.path.join(YG, "Visual Tone - Essential Flow Sound Effects.rar")
SRC_SM = os.path.join(YG, "Sound Morph - Sinematic")
DEST_SM = os.path.join(B1, "Sound Morph - Sinematic")
VTDIR = os.path.join(B1, "Visual Tone - Essential Flow Sound Effects")
LOG = os.path.join(ORG, "fix_yugao_20260919.log")
EXPECT_BYTES = 343486297

out = []
def log(s=""):
    print(s, flush=True); out.append(s)

def finish_and_exit(code):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("== 预告修正 %s ==\n" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        f.write("\n".join(out) + "\n----------\n")
    sys.exit(code)

log("== 预告修正 ==")

# 0) 前置检查
if not os.path.isdir(SRC_SM): log("!! 缺源 %s" % SRC_SM); finish_and_exit(1)
if os.path.exists(DEST_SM): log("!! 目标已存在 %s" % DEST_SM); finish_and_exit(1)
if not os.path.isfile(RAR): log("!! 缺 rar"); finish_and_exit(1)

# 1) 移动 Sinematic
rc = subprocess.run(["mv", "-v", SRC_SM, DEST_SM], capture_output=True, text=True)
log("1) 移动: rc=%d | %s" % (rc.returncode, (rc.stdout + rc.stderr).strip()))
if rc.returncode != 0 or not os.path.isdir(DEST_SM) or os.path.exists(SRC_SM):
    log("!! 移动失败"); finish_and_exit(1)

# 2) rar 完整性测试
t = subprocess.run(["unrar", "t", "-p-", RAR], capture_output=True, text=True)
log("2) unrar 测试: rc=%d" % t.returncode)
if t.returncode != 0:
    log("!! rar 测试失败（不删 rar）"); log(t.stdout[-600:]); finish_and_exit(1)

# 3) 解压到 01
x = subprocess.run(["unrar", "x", "-p-", "-o-", RAR, B1 + "/"], capture_output=True, text=True)
log("3) 解压: rc=%d" % x.returncode)
log("   " + "\n   ".join(x.stdout.strip().splitlines()[-6:]))
if x.returncode != 0 or not os.path.isdir(VTDIR):
    log("!! 解压失败（不删 rar）"); finish_and_exit(1)

# 4) 核验：字节总和 + 文件数
n = s = 0
for root, dirs, fns in os.walk(VTDIR):
    for fn in fns:
        p = os.path.join(root, fn)
        n += 1; s += os.path.getsize(p)
log("4) 提取核验: %d 件 / %d B（rar 清单 343486297 B）" % (n, s))
if s != EXPECT_BYTES:
    log("!! 字节数不符差额 %d，中止（不删 rar）" % (s - EXPECT_BYTES)); finish_and_exit(1)
log("   字节级一致 ✓")

# 5) sha256 留档 → 删 rar
h = hashlib.sha256()
with open(RAR, "rb") as f:
    while True:
        b = f.read(1 << 22)
        if not b: break
        h.update(b)
log("5) rar sha256=%s" % h.hexdigest())
os.remove(RAR)
log("   已删 rar")

# 6) 收壳
rest = os.listdir(YG)
log("6) 预告 剩余: %r" % rest)
if not rest:
    os.rmdir(YG)
    log("   空壳已移除")

# 7) 映射表维护段
with open(os.path.join(ORG, "整理映射表.md"), "a", encoding="utf-8") as f:
    f.write("\n## 维护记录（2026-09-19 · 预告修正）\n\n")
    f.write("- `03_项目素材/预告/Sound Morph - Sinematic/`（432 件）→ `01_商业音效包/Sound Morph - Sinematic/`\n")
    f.write("- `Visual Tone - Essential Flow Sound Effects.rar`（144 条目 / 343,486,297 B）→ 解压为 `01_商业音效包/Visual Tone - Essential Flow Sound Effects/` → 字节核验一致后删 rar（sha256 见 fix_yugao_20260919.log）\n")
    f.write("- 空壳 `预告/` 已移除；`03_项目素材` 现只含 LTT_V30All\n")
log("7) 映射表已追加维护段")

# 8) 终态
log("8) 终态:")
for line in sorted(os.listdir(B1)):
    log("   01/ " + line)
log("   03/ " + " / ".join(sorted(os.listdir(os.path.join(LIB, "03_项目素材")))))
finish_and_exit(0)
