# -*- coding: utf-8 -*-
import json, os, hashlib
LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"
DED = "/volume1/主目录/Hermes/read/Projects/sfx-browser/dedup"
d = json.load(open(os.path.join(DED, "scan_quick.json"), encoding="utf-8"))
cl = d["clusters"]
def find(sub):
    for c in cl:
        for m in c["members"]:
            if sub in m: return c
def blk(p, off, ln):
    sz = os.path.getsize(p)
    with open(p, "rb") as f:
        if off == "tail": f.seek(max(0, sz - ln))
        else: f.seek(off)
        return f.read(ln)
for name, sub in [("c1-BullRoar", "临时/23 Bull Roar.wav"),
                  ("c2-SPF052", "PREL_SSFX_COMP_SP02.52.C.wav"),
                  ("c3-SPO009", "PREL_SSFX_ASCEND_PO01.9.C.wav"),
                  ("c4-IE027", "SSFX_IE_027.R.wav")]:
    c = find(sub)
    if not c: print(name, "NOT FOUND"); continue
    print("== %s: count=%d size=%d ==" % (name, c["count"], c["size"]))
    for m in c["members"][:3]:
        p = os.path.join(LIB, m)
        head = blk(p, 0, 65536); tail = blk(p, "tail", 65536)
        mid = blk(p, c["size"] // 2, 65536)
        z = lambda b: sum(1 for x in b[:4096] if x == 0) / 4096
        print("   sz=%d h0=%.2f t0=%.2f | h=%s t=%s m=%s | %s" % (
            os.path.getsize(p), z(head), z(tail),
            hashlib.md5(head).hexdigest()[:8], hashlib.md5(tail).hexdigest()[:8],
            hashlib.md5(mid).hexdigest()[:8], m[:66]))
