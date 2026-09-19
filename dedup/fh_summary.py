# -*- coding: utf-8 -*-
import json
d = json.load(open("/volume1/主目录/Hermes/read/Projects/sfx-browser/dedup/fullhash.json", encoding="utf-8"))
s = d["summary"]; cl = d["clusters"]
print("SUMMARY:", json.dumps(s, ensure_ascii=False))
print()
print("== 真实(全量md5确认) TOP8 浪费簇 ==")
for c in cl[:8]:
    print("[%7.0f MiB] %d份×%.1fMiB ｜ %s" % (c["waste"]/2**20, c["count"], c["size"]/2**20, c["members"][0][:72]))
print()
print("== 四个原误报簇的最终真相 ==")
def find(sub):
    for c in cl:
        for m in c["members"]:
            if sub in m: return c
for sub in ["23 Bull Roar", "PREL_SSFX_COMP_SP02.52.C", "PREL_SSFX_ASCEND_PO01.9.C", "SSFX_IE_027.R"]:
    c = find(sub)
    print("  %-30s -> %s" % (sub[:28], ("真重复: 簇 %d 份" % c["count"]) if c else "查无重复(误报确认)"))
