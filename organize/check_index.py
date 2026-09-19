#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""索引核验：表结构 + 计数 + 抽查新路径"""
import sqlite3
DB = "/volume1/主目录/Hermes/read/Projects/sfx-browser/data/sfx.db"
c = sqlite3.connect(DB)
tabs = [r[0] for r in c.execute("select name from sqlite_master where type='table'").fetchall()]
print("tables:", tabs)
for t in tabs:
    try:
        print(" ", t, "=", c.execute("select count(*) from %s" % t).fetchone()[0])
    except Exception as e:
        print(" ", t, "ERR", e)
try:
    rows = c.execute("select * from files limit 3").fetchall()
    for r in rows: print("sample:", str(r)[:170])
except Exception as e:
    print("sample err:", e)
try:
    n = c.execute("select count(*) from files where path like '01_商业音效包/%'").fetchone()[0]
    print("01_商业音效包 路径前缀样本数:", n)
    n2 = c.execute("select count(*) from files where path like '02_中文音效合集/%'").fetchone()[0]
    print("02_中文音效合集:", n2)
except Exception as e:
    print("prefix query err:", e)
