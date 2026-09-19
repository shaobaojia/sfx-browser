# -*- coding: utf-8 -*-
import json, sys
d = json.load(open("/volume1/主目录/Hermes/read/Projects/sfx-browser/dedup/fullhash.json", encoding="utf-8"))
s = d["summary"]
try:
    assert s["errors"] == 0
    assert 10000 <= s["true_clusters"] <= 100000
    assert 10000 <= s["true_excess_files"] <= 100000
    assert 50e9 <= s["true_excess_bytes"] <= 220e9
    print("GUARD-OK clusters=%d files=%d GiB=%.1f" % (s["true_clusters"], s["true_excess_files"], s["true_excess_bytes"]/2**30))
except AssertionError as e:
    print("GUARD-FAIL", e); sys.exit(1)
