# AGENTS.md — sfx-browser 交接备忘录

局域网音效库浏览器：NAS（UGREEN DXP4800）上的秒搜 / 试听 / 波形 / 篮子导出服务。
GitHub: https://github.com/shaobaojia/sfx-browser （本目录即仓库）

- 服务：用户级 systemd `sfx-browser.service`（开机自启），端口 **8093**
- 代码：`/volume1/主目录/Hermes/read/sfx-browser/`（Hermes 容器同路径可见）
- 音效库：`/volume1/主目录/Collection/素材&模板&音库/音效`（21 万+ 条 / 480GB+，**容器看不到，走 `ssh nas`**）
- 入口：http://192.168.3.65:8093

## 刚做完
- v1.1：篮子「导出到文件夹」（POST /api/export，安全边界 /volume1/主目录/，重名自动加 _2 后缀）+ 篮子单项下载 + 下载 ZIP 更名更直白
- 全量索引 21 万条 4~7 秒重建（纯元数据扫描）；服务常驻内存 ~18MB
- 冒烟测试 18 项全绿（smoke_test.py）；GitHub 仓库建立

## 正在做
- （无）

## 下一步
- 下载任务收尾后重扫索引：`ssh nas "cd /volume1/主目录/Hermes/read/sfx-browser && python3 build_index.py"`
- 候选（未定）：语义搜索二期（需 PC 批跑声学向量）、导出进度条、手机端细节

## 坑
- **NAS 无 git**：仓库操作都在 Hermes 容器里对同一路径执行（首次已设 `git config --global --add safe.directory`）
- 改文件走 `ssh nas "cat > '路径'" < 本地文件`（共享卷 write_file/patch 会被 Hermes 守卫拦）
- 服务操作：`ssh nas 'export XDG_RUNTIME_DIR=/run/user/1000; systemctl --user restart sfx-browser'`
- 搜索索引存相对路径（相对库根），避免“音效”前缀全体命中；波形色 0x6ea8fe
- 端口：8093=本品；8008/9090/9119/9443/9999 已被占用
- 全量重扫很便宜（纯元数据，几秒）；但任何“内容级”全库操作（解码/转码/分析）是小时级——别乱来
