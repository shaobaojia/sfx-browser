#!/bin/bash
LIB="/volume1/主目录/Collection/素材&模板&音库/音效"
ORG="/volume1/主目录/Hermes/read/Projects/sfx-browser/organize"
YG="$LIB/03_项目素材/预告"

echo "=== ① 预告 一级清单 ==="
ls -la "$YG" | head -50
echo
echo "=== ② 规模 ==="
echo "总文件数: $(find "$YG" -type f | wc -l)"
du -sh "$YG"
echo
echo "=== ③ 二级目录 ==="
find "$YG" -mindepth 2 -maxdepth 2 -type d | sed "s|$YG/||" | sort | head -80
echo
echo "=== ④ 各子项概况 ==="
for d in "$YG"/*; do
  if [ -d "$d" ]; then printf '%7d 件  %s\n' "$(find "$d" -type f | wc -l)" "$(basename "$d")";
  elif [ -f "$d" ]; then printf '  [文件]  %s (%s B)\n' "$(basename "$d")" "$(stat -c %s "$d")"; fi
done
echo
echo "=== ⑤ 压缩包普查（预告全子树） ==="
find "$YG" \( -iname "*.rar" -o -iname "*.zip" -o -iname "*.7z" \) -exec ls -la {} \;
echo
echo "=== ⑥ rar 内容 ==="
for R in "$YG"/*.rar; do
  [ -e "$R" ] || { echo "(顶层无 rar)"; break; }
  echo ">> $(basename "$R")"
  N=$(unrar lb -p- "$R" 2>/dev/null | wc -l)
  echo "条目总数: $N"
  echo "--- 前 25 项 ---"
  unrar lb -p- "$R" 2>/dev/null | head -25
  echo "--- 顶层分布 ---"
  unrar lb -p- "$R" 2>/dev/null | sed 's|\\|/|g' | awk -F/ '{print $1}' | sort | uniq -c | sort -rn | head -15
done
echo
echo "=== ⑦ recon 里关于 预告 ==="
grep -n "预告" "$ORG/recon_20260919.txt" | head -40
echo
echo "=== ⑧ 01 商业音效包 顶层（对照） ==="
ls "$LIB/01_商业音效包"
echo
echo "=== ⑨ Sound Morph 相关全集 ==="
find "$LIB" -maxdepth 3 -iname "*sound morph*" -o -maxdepth 3 -iname "*sinematic*" 2>/dev/null | head -20
echo
echo "=== DONE ==="
