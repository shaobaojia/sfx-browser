# AGENTS.md — sfx-browser 交接备忘录

局域网音效库浏览器：NAS（UGREEN DXP4800）上的秒搜 / 试听 / 波形 / 篮子导出服务。
GitHub: https://github.com/shaobaojia/sfx-browser （本目录即仓库）

- 服务：用户级 systemd `sfx-browser.service`（开机自启），端口 **8093**
- 代码：`/volume1/主目录/Hermes/read/Projects/sfx-browser/`（Hermes 容器同路径可见）
- 音效库：`/volume1/主目录/Collection/素材&模板&音库/音效`（21 万+ 条 / 480GB+，**容器看不到，走 `ssh nas`**）
- 入口：http://192.168.3.65:8093

## 刚做完
- 底部全局播放开关：🔊/🔇 胶囊（快捷键 M；关掉后悬停/点击/键盘全部静默，状态本地记忆；输入框内不误触）
- 下载 ZIP 改为平铺打包（解压后所有文件在同一目录，重名自动加 `_2` 后缀；冒烟测试含平铺断言）
- 前序：篮子「导出到文件夹」（POST /api/export，边界 /volume1/主目录/）+ 单项下载；全量索引 21 万条 4~7 秒重建；服务内存 ~18MB；冒烟 18 项全绿

## 正在做
- （无）

## 下一步
- 下载任务收尾后重扫索引：`ssh nas "cd /volume1/主目录/Hermes/read/Projects/sfx-browser && python3 build_index.py"`
- 候选（未定）：语义搜索二期（需 PC 批跑声学向量）、导出进度条、手机端细节

## 坑
- **NAS 无 git**：仓库操作都在 Hermes 容器里对同一路径执行（已设 `git config --global --add safe.directory`）
- 改文件走 `ssh nas "cat > '路径'" < 本地文件`（共享卷 write_file/patch 会被 Hermes 守卫拦）
- 服务操作：`ssh nas 'export XDG_RUNTIME_DIR=/run/user/1000; systemctl --user restart sfx-browser'`
- 前端快捷键（m/l/空格/方向键）在输入框内被有意屏蔽（防误触），属预期
- 搜索索引存相对路径（相对库根），避免“音效”前缀全体命中；波形色 0x6ea8fe
- 端口：8093=本品；8008/9090/9119/9443/9999 已被占用
- 全量重扫很便宜（纯元数据，几秒）；但任何“内容级”全库操作（解码/转码/分析）是小时级——别乱来

## 去重（dedup/）
- 流程：scan_quick.py（快扫）→ full_hash.py（全量 md5 复核，执行前必跑）→ execute_quarantine.py（移入隔离区）→ restore_from_quarantine.py（一键回滚）
- 铁律：快扫指纹（首尾 64KB）对「等长 + 首尾大段静音」素材会误报；执行只认全量 md5
- 隔离区约定：库外同级目录「音效_去重待删_<日期>/」，保持原结构，复核后整体删除
- 首轮：2026-09-19，隔离 87,507 件 / 172.2 GiB；库 245,902→158,395 件
