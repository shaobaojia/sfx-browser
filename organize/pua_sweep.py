#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全库 PUA 残渣终极扫描（E000-F8FF + U+FFFD），列出所有残留"""
import os

LIB = "/volume1/主目录/Collection/素材&模板&音库/音效"

def bad(s):
    return [hex(ord(c)) for c in s if 0xE000 <= ord(c) <= 0xF8FF or ord(c) == 0xFFFD]

hits = 0
for root, dirs, fns in os.walk(LIB):
    for nm in list(dirs) + fns:
        b = bad(nm)
        if b:
            hits += 1
            print("%s | %r" % (b, os.path.join(root, nm).replace(LIB + "/", "")))
print("PUA/替换符 残留对象: %d" % hits)
print("DONE")
