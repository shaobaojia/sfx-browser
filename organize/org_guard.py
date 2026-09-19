#!/usr/bin/env python3
import json, sys
d = json.load(open("/volume1/主目录/Hermes/read/Projects/sfx-browser/organize/organize_dry.json", encoding="utf-8"))
ok = bool(d.get("guard_ok")) and d.get("unmatched_count", 1) == 0 and d.get("planned", 0) > 100000 and d.get("conflict_count", 99999) < 2000
print(("GUARD-PASS " if ok else "GUARD-FAIL ") + json.dumps(d, ensure_ascii=False))
sys.exit(0 if ok else 1)
