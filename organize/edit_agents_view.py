#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 在 AGENTS.md 的「前端快捷键」条目后追加波形交互行
import io
P = '/volume1/主目录/Hermes/read/Projects/sfx-browser/AGENTS.md'
txt = io.open(P, encoding='utf-8').read()
anchor = '- 前端快捷键（m/l/空格/方向键）在输入框内被有意屏蔽（防误触），属预期\n'
assert txt.count(anchor) == 1, '锚点次数=%d' % txt.count(anchor)
if '波形交互（v1.3）' in txt:
    print('already present')
else:
    new = anchor + '- 波形交互（v1.3）：缩略图尺寸=顶部「波形」滑杆（水平，120–800px，宽高 10:1）+「行高」滑杆（垂直，18–72px）；CSS 变量 --wavew/--rowh，localStorage: sfx_wavew/sfx_rowh。缩略图与面板波形支持点击跳播 + 拖动扫播（跨文件跳播用 pendingSeek/loadedmetadata）；播放头红线随播放走（rAF）；波形底图 960×96（cache 键 _v960；前端 URL 带 &r=2 破旧缓存）\n'
    txt = txt.replace(anchor, new)
    io.open(P, 'w', encoding='utf-8').write(txt)
    print('AGENTS.md updated')
