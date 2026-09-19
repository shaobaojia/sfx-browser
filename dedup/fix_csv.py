# -*- coding: utf-8 -*-
import re, csv
p = "/volume1/主目录/Hermes/read/Projects/sfx-browser/dedup/full_md5.csv"
rx = re.compile(r"^(.*),(\d+),([0-9a-f]{32})$")
rows = []; bad = 0
with open(p, encoding="utf-8-sig") as f:
    next(f, None)
    for line in f:
        m = rx.match(line.rstrip("\r\n"))
        if m: rows.append(m.groups())
        else: bad += 1
with open(p + ".clean", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["rel","size","md5"]); w.writerows(rows)
print("fixed rows=%d unparsed=%d" % (len(rows), bad))
