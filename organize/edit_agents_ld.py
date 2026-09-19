#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 在 AGENTS.md 的 r3 工具链行后追加 LD 归一记录行
import io
P = '/volume1/主目录/Hermes/read/Projects/sfx-browser/AGENTS.md'
txt = io.open(P, encoding='utf-8').read()
anchor = '`r3_对换记录_Multiply_20260919.md`\n'
assert txt.count(anchor) == 1, '锚点次数=%d' % txt.count(anchor)
if 'LD 归一（2026-09-19）' in txt:
    print('already present')
else:
    new = anchor + '- **LD 归一（2026-09-19）**：`02_中文音效合集/大气深沉1~6` + `气氛音乐音效` = 品牌 **Lens Distortions** 六产品被卖家改名重打包 → 归一 `01_商业音效包/Lens Distortions/`（目录名保留中文注释：`英文名（大气深沉N · 原注释）`）；搬入 2,528 件 / 0 失败；工具 `ld_merge.py`（--dry/--execute）｜日志 `ld_move_log.csv`｜回滚 `ld_rollback.py`｜记录 `LD归一记录_20260919.md`\n'
    txt = txt.replace(anchor, new)
    io.open(P, 'w', encoding='utf-8').write(txt)
    print('AGENTS.md updated')
