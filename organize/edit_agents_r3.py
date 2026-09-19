#!/usr/bin/env python3
# AGENTS.md 更新：Multiply Sound 对换扶正（r3）
P = '/volume1/主目录/Hermes/read/Projects/sfx-browser/AGENTS.md'
text = open(P, encoding='utf-8').read()

B1 = ('- **2026-09-19 Multiply Sound 对换扶正（用户拍板）**：@影采 V1/V2 注解版 **2,216 件 / 16 GiB** '
      '自隔离区 r2 原路回库 → 恢复完整注解全家桶（**4,246 件 / ≈71 GiB**）；01 旧份《Multiply Sound Film Score Bundle》'
      '**2,219 件** 对换入隔离区「主库旧份对换/」（含 3 件同名不同内容版本差异件）；隔离区 8,175 → **8,178 件**；'
      '索引 **172,257**；实测「连复段」「Ghostly」直落 04 注解路径。详见 `organize/r3_对换记录_Multiply_20260919.md`')
B2 = ('- **2026-09-19 双 rar 验收**：`Multiply Sound@影采` 两 rar 逐成员 CRC32 对档 — Vol.3 **1,120/1,120（100%）**、'
      'CHPTRS **883/884（唯一例外 = 116B 站方推广链接）** → **合格可删，待拍板**（`organize/rar_audit_result.json`；'
      '⚠️ 7zz 打不开此类 RAR5，用 unrar）')

def rep(old, new):
    global text
    n = text.count(old)
    assert n == 1, 'anchor x%d: %r' % (n, old[:60])
    text = text.replace(old, new)

rep('## 刚做完\n- **2026-09-19 并库 r2（两邻居合并）**',
    '## 刚做完\n' + B1 + '\n' + B2 + '\n- **2026-09-19 并库 r2（两邻居合并）**')

rep('（**8,175 件 / 58.17 GiB，删留待拍板**）',
    '（**8,175 件 / 58.17 GiB，删留待拍板；后经 Multiply 对换调整为 8,178 件，见上**）')

rep('- **待拍板**：隔离区 r2（8,175 件 / 58.17 GiB）删或留；`Multiply Sound@影采` 内含 2 个未解 rar（原样保留，未解压）',
    '- **待拍板**：① 隔离区 r2（现 8,178 件 / 约 58 GiB）删或留；② `Multiply Sound@影采` 2 个 rar（已核验内容 100% 在库）删或留')

rep('；回滚 `organize/r2_rollback.py`）',
    '；回滚 `organize/r2_rollback.py`；后经 Multiply 对换，现 **8,178 件**）')

rep('日志 `r2_quarantine_moved.csv` + `r2_merge_moved.csv`',
    '日志 `r2_quarantine_moved.csv` + `r2_merge_moved.csv`｜**r3 对换**：`r3_swap_restore.csv` / `r3_swap_out.csv`'
    '｜`r3_swap_rollback.py`（回滚）｜`rar_audit.py`（rar 逐成员 CRC 验收）｜`r3_对换记录_Multiply_20260919.md`')

open(P, 'w', encoding='utf-8').write(text)
print('AGENTS.md updated OK')
