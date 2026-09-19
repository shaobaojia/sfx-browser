#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修正 organize_moved.csv：多源冲突组中被覆盖的行标记为 conflict-lost（不可回滚）。
同时导出 organize_lost_files.json 完整记录。"""
import os, csv, json
from collections import OrderedDict
ORG = "/volume1/主目录/Hermes/read/Projects/sfx-browser/organize"
MOVED = os.path.join(ORG, "organize_moved.csv")

rows = list(csv.reader(open(MOVED, encoding="utf-8-sig")))
hdr, data = rows[0], rows[1:]

g = OrderedDict()
for i, r in enumerate(data):
    if r[2] == "conflict":
        g.setdefault(r[1], []).append(i)

lost_records = []
for nr, idxs in g.items():
    for i in idxs[:-1]:
        lost_records.append({"rel": data[i][0], "intended": data[i][1], "note": "被后续同目标搬迁覆盖，原内容唯一，不可回滚"})
        data[i][2] = "conflict-lost"

with open(MOVED + ".tmp", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(hdr); w.writerows(data)
os.replace(MOVED + ".tmp", MOVED)

json.dump(lost_records, open(os.path.join(ORG, "organize_lost_files.json"), "w"), ensure_ascii=False, indent=1)

print("标记 conflict-lost:", len(lost_records))
for r in lost_records:
    print("  ", r["rel"])
n_conf = sum(1 for r in data if r[2] == "conflict")
n_moved = sum(1 for r in data if r[2] == "moved")
n_lost = sum(1 for r in data if r[2] == "conflict-lost")
print("moved=%d conflict=%d conflict-lost=%d" % (n_moved, n_conf, n_lost))
