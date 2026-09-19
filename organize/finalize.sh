#!/bin/bash
# 整理收官：修正记录 → 回滚演练 → 快照探测 → 重建索引 → 核验 → 计数 → 映射表
cd /volume1/主目录/Hermes/read/Projects/sfx-browser/organize || exit 1
LIB="/volume1/主目录/Collection/素材&模板&音库/音效"

echo "===== 1. 修正 moved.csv（标记12个conflict-lost）====="
python3 fix_movedcsv.py
echo
echo "===== 2. 回滚演练 ====="
python3 organize_rollback.py --dry
echo
echo "===== 3. 快照/文件系统探测 ====="
df -T "$LIB" | tail -1
for d in "#snapshot" ".snapshots" "@snapshots" "#recycle"; do
  [ -d "/volume1/主目录/$d" ] && echo "FOUND: /volume1/主目录/$d" && ls "/volume1/主目录/$d" 2>/dev/null | head -8
done
ls -a "/volume1/主目录/" | grep -E '^\.|snap|recycle|#' | head -15
command -v btrfs >/dev/null && (btrfs subvolume list /volume1 2>&1 | head -10) || echo "(no btrfs cmd)"
echo
echo "===== 4. 重建索引 ====="
cd /volume1/主目录/Hermes/read/Projects/sfx-browser
time python3 build_index.py
echo
echo "===== 5. 索引核验 ====="
python3 check_index.py
echo
echo "===== 6. 桶计数 ====="
for b in "01_商业音效包" "02_中文音效合集" "03_项目素材" "99_待整理"; do
  n=$(find "$LIB/$b" -type f 2>/dev/null | wc -l)
  echo "$b : $n 个文件"
done
echo "TOTAL: $(find "$LIB" -type f | wc -l)  (预期 162419)"
echo "顶层项数: $(ls "$LIB" | wc -l)"
echo "冲突区: $(find "$LIB/99_待整理/_命名冲突" -type f | wc -l) 个"
echo
echo "===== 7. 空间 ====="
du -sh "$LIB"/0* "$LIB"/9* 2>/dev/null
du -sh "$LIB" 2>/dev/null
echo
echo "===== 8. 映射表 ====="
cd /volume1/主目录/Hermes/read/Projects/sfx-browser/organize
python3 make_mapping_md.py
ls -la "整理映射表.md" 2>/dev/null
echo
echo "===== 9. 服务抽查 ====="
echo -n "HTTP: "; curl -s -o /dev/null -w "%{http_code}\n" "http://127.0.0.1:8093/"
curl -s "http://127.0.0.1:8093/api/search?q=door" | head -c 260; echo
echo
echo "===== 完成 ====="
